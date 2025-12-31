from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class ProductPagination(PageNumberPagination):
    page_size = 24  # Default items per page
    page_size_query_param = 'page_size'
    max_page_size = 72
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,  # Total: 120
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'page_size': self.page.paginator.per_page,
            'total_pages': self.page.paginator.num_pages,  # 5 pages
            'current_page': self.page.number,  # Current page: 1
            'results': data  # The actual products
        })