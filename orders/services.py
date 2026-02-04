"""
Order services - Business logic for order operations
"""
from decimal import Decimal
from django.utils import timezone
from .models import Order, OrderItem
from product.models import Deal, Product, ProductVariant

class ComboService:
    """Service for handling combo operations in orders"""
    
    @staticmethod
    def get_combo_total_price(combo):
        """
        Calculate total price of all items in a combo
        
        Args:
            combo: ProductCombo instance
        
        Returns:
            Decimal: Total price of combo items
        """
        total = Decimal(0)
        for combo_item in combo.items.all():
            product = combo_item.product
            total += product.base_price * combo_item.quantity
        return total
    
    @staticmethod
    def get_combo_discount(combo):
        """
        Calculate discount for combo vs buying items separately
        
        Args:
            combo: ProductCombo instance
        
        Returns:
            dict with keys: regular_price, selling_price, discount_amount, discount_percent
        """
        regular_price = ComboService.get_combo_total_price(combo)
        selling_price = combo.combo_selling_price or regular_price
        discount_amount = regular_price - selling_price
        discount_percent = 0
        
        if regular_price > 0:
            discount_percent = int((discount_amount / regular_price) * 100)
        
        return {
            'regular_price': regular_price,
            'selling_price': selling_price,
            'discount_amount': discount_amount,
            'discount_percent': discount_percent
        }
    
    @staticmethod
    def create_combo_order_items(order, combo, quantity=1):
        """
        Create order items from a combo
        Creates a parent item representing the combo, plus child items for each product
        
        Args:
            order: Order instance
            combo: ProductCombo instance
            quantity: Number of combo bundles to order
        
        Returns:
            dict: {
                'combo_parent': Parent OrderItem instance,
                'items': List of child OrderItem instances,
                'total_price': Total price of all items in combo
            }
        
        Raises:
            ValueError: If inputs are invalid
        """
        if not combo.is_active:
            raise ValueError("Combo is not active")
        
        # Create parent item representing the combo
        combo_pricing = ComboService.get_combo_discount(combo)
        
        combo_parent = OrderItem.objects.create(
            order=order,
            product=combo.main_product,
            combo=combo,
            product_name=combo.name,
            quantity=quantity,
            original_price=combo_pricing['regular_price'],
            price=combo_pricing['selling_price'],
            discount_percent=combo_pricing['discount_percent'],
            is_combo_parent=True
        )
        
        # Create child items for each product in combo
        child_items = []
        for combo_item in combo.items.all():
            product = combo_item.product
            item_quantity = combo_item.quantity * quantity
            
            child_item = OrderItem.objects.create(
                order=order,
                product=product,
                combo=combo,
                combo_parent=combo_parent,
                product_name=product.name,
                quantity=item_quantity,
                original_price=product.base_price,
                price=product.base_price,
                discount_percent=0,
                is_combo_parent=False
            )
            child_items.append(child_item)
        
        total_price = combo_pricing['selling_price'] * quantity
        
        return {
            'combo_parent': combo_parent,
            'items': child_items,
            'total_price': total_price
        }




class OrderService:
    """Service for handling order operations including deals"""
    
    @staticmethod
    def calculate_item_price(product, product_variant, deal=None):
        """
        Calculate the final price for an order item
        
        Args:
            product: Product instance
            product_variant: ProductVariant instance (optional)
            deal: Deal instance (optional)
        
        Returns:
            dict with keys: original_price, final_price, discount_percent
        """
        # Get base price
        if product_variant:
            original_price = product_variant.price
        else:
            original_price = product.base_price
        
        final_price = original_price
        discount_percent = 0
        
        # Apply deal discount if exists
        if deal:
            discount_percent = deal.discount_percent
            final_price = original_price * Decimal(100 - discount_percent) / Decimal(100)
        
        return {
            'original_price': original_price,
            'final_price': final_price,
            'discount_percent': discount_percent
        }
    
    @staticmethod
    def create_order_item(order, product=None, product_variant=None, quantity=1, deal=None):
        """
        Create an order item with optional deal
        
        Args:
            order: Order instance
            product: Product instance
            product_variant: ProductVariant instance
            quantity: Quantity to order
            deal: Deal instance (optional)
        
        Returns:
            OrderItem instance
        
        Raises:
            ValueError: If inputs are invalid
        """
        if not product and not product_variant:
            raise ValueError("Either product or product_variant must be provided")
        
        if product and product_variant:
            raise ValueError("Provide either product or product_variant, not both")
        
        if not product:
            product = product_variant.product
        
        # Validate deal
        if deal:
            now = timezone.now()
            
            if not deal.is_active:
                raise ValueError("Deal is not active")
            
            if not (deal.start_at <= now <= deal.end_at):
                raise ValueError("Deal is not currently available")
            
            if deal.product != product:
                raise ValueError("Deal does not apply to this product")
            
            if deal.remaining_quantity < quantity:
                raise ValueError(f"Insufficient deal inventory. Only {deal.remaining_quantity} items remaining.")
        
        # Calculate prices
        pricing = OrderService.calculate_item_price(product, product_variant, deal)
        
        # Create order item
        order_item = OrderItem.objects.create(
            order=order,
            product=product,
            product_variant=product_variant,
            deal=deal,
            product_name=product.name,
            variant_name=product_variant.variant_attributes.all() if product_variant else None,
            quantity=quantity,
            original_price=pricing['original_price'],
            price=pricing['final_price'],
            discount_percent=pricing['discount_percent'],
        )
        
        return order_item
    
    @staticmethod
    def finalize_order_deals(order):
        """
        Finalize deals after order is confirmed
        - Increment deal sold quantities
        - Update deal purchase counts
        
        Args:
            order: Order instance
        """
        for item in order.items.filter(deal__isnull=False, is_combo_parent=False):
            deal = item.deal
            
            # Increment sold quantity
            deal.increment_sold(item.quantity)
            
            # Increment purchase count (now in Deal model directly)
            deal.increment_purchases(item.quantity)
    
    @staticmethod
    def finalize_order_combos(order):
        """
        Finalize combos after order is confirmed
        - Decrement combo item inventory (reduce variant stock)
        
        Args:
            order: Order instance
        """
        for item in order.items.filter(combo__isnull=False, is_combo_parent=False):
            combo = item.combo
            product = item.product
            
            # Reduce product variant stock if available
            try:
                # Try to find an active variant for the product
                variant = product.variants.filter(is_active=True).first()
                if variant and variant.stock_quantity >= item.quantity:
                    variant.stock_quantity -= item.quantity
                    variant.sold_quantity += item.quantity
                    variant.save(update_fields=['stock_quantity', 'sold_quantity'])
            except:
                pass
    
    @staticmethod
    def can_use_deal(deal, quantity=1):
        """
        Check if a deal can be used for a purchase
        
        Args:
            deal: Deal instance
            quantity: Quantity to check
        
        Returns:
            tuple: (is_valid, error_message)
        """
        now = timezone.now()
        
        if not deal.is_active:
            return False, "Deal is not active"
        
        if not (deal.start_at <= now <= deal.end_at):
            return False, "Deal is not currently available"
        
        if deal.remaining_quantity < quantity:
            return False, f"Insufficient inventory. Only {deal.remaining_quantity} items available."
        
        return True, None
