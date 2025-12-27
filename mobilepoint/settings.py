from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-smj3k7)x+j#onq0_$huba-5_9xp=v+kords^n5diz02yw1wpr8'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*']


AUTH_USER_MODEL = "accounts.User"
X_FRAME_OPTIONS = "SAMEORIGIN"

# Application definition

INSTALLED_APPS = [
    'dashub',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_filters',
    'corsheaders',
    'rest_framework',
    'accounts',
    'product',
    'tinymce',
    'filehub',
    'orders',
    'wishlist',
    'website',
]

# REST Framework Configuration
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}

# JWT Configuration
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}

# CORS Settings (adjust for production)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    'https://api.gowell.edu.np/',
    'https://mobilepoint-seven.vercel.app/',
    
]
CSRF_COOKIE_SECURE = False
SESSION_COOKIE_SECURE = False


MIDDLEWARE = [
    
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mobilepoint.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'mobilepoint.wsgi.application'


# Database
# https://docs.djangoproject.com/en/6.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/6.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/6.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/6.0/howto/static-files/
STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "assets")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]


MEDIA_ROOT = os.path.join(BASE_DIR, "media")
MEDIA_URL = "/media/"

DASHUB_SETTINGS = {
    "site_logo": "/static/logo.svg",
    "site_icon": "/static/favicon.ico",
    "theme_color": "#31aa98",
    "border_radius": "5px",
    "hide_models": [
        "auth",  # Hides all models in the auth app
        "auth.group"  # Hides the group model in the auth app
    ],
    "custom_links": {
        "auth": [
            {
                "model": "auth.post" # Links directly to the auth.post model
            },
            {
                "name": "User Management",
                "icon": "fa-solid fa-users",
                "submenu": [
                    {"model": "auth.user", "order": 1},
                    {"model": "auth.group", "order": 2}
                ]
            }
        ],
    },
    "submenus_models": ["auth.group"],
    "default_orders": {
        "auth": 10,
        "auth.group": 4,
    },
    "icons": {
        
        'accounts.user': 'hgi hgi-stroke hgi-user',
        'accounts.usergroup': 'hgi hgi-stroke hgi-users',
        "product": "hgi hgi-stroke hgi-shopping-bag",

        # Core catalog
        "product.category": "hgi hgi-stroke hgi-grid-view",
        "product.brand": "hgi hgi-stroke hgi-crown",
        # "product.product": "hgi hgi-stroke hgi-box",
        "product.product": "hgi hgi-stroke hgi-shopping-basket-check-in-01",

        # Variants system
        "product.variantattribute": "hgi hgi-stroke hgi-settings-02",
        "product.variantattributevalue": "hgi hgi-stroke hgi-arc-browser",
        "product.productvariant": "hgi hgi-stroke hgi-layers-01",
        "product.productvariantattributevalue": "hgi hgi-stroke hgi-link-02",

        # Media
        "product.productimage": "hgi hgi-stroke hgi-image-01",

        # Promotions & deals
        "product.productpromotion": "hgi hgi-stroke hgi-gift",
        "product.deal": "hgi hgi-stroke hgi-flash",

        # Merchandising
        "product.frequentlyboughttogether": "hgi hgi-stroke hgi-repeat",
        "product.productcomparison": "hgi hgi-stroke hgi-agreement-01",
        # Orders
    "orders.order": "hgi hgi-stroke hgi-invoice-01",
    "orders.orderitem": "hgi hgi-stroke hgi-list-view",
    "orders.orderstatushistory": "hgi hgi-stroke hgi-time-quarter",

    # Wishlist
    "wishlist.wishlist": "hgi hgi-stroke hgi-favourite",
    "wishlist.wishlistitem": "hgi hgi-stroke hgi-heart-add",
    # Website app
    "website.carousel": "hgi hgi-stroke hgi-sliders-01",
    "website.carouselslide": "hgi hgi-stroke hgi-image-01",
    "website.advertisement": "hgi hgi-stroke hgi-megaphone",
    "website.banner": "hgi hgi-stroke hgi-flag",
    "website.testimonial": "hgi hgi-stroke hgi-user-voice",
    "website.faq": "hgi hgi-stroke hgi-question-circle",
    "website.newslettersubscriber": "hgi hgi-stroke hgi-mail",
    "website.contactmessage": "hgi hgi-stroke hgi-mail-open",
    "website.sitesettings": "hgi hgi-stroke hgi-settings-02",
    },
    "custom_js": [
        "/static/js/admin.js",
    ],
    "custom_css": [
        "/static/css/admin.css",
    ]
}


TINYMCE_JS_URL = "https://cdnjs.cloudflare.com/ajax/libs/tinymce/7.5.1/tinymce.min.js"
TINYMCE_DEFAULT_CONFIG = {
    "promotion": False,
    "menubar": "file edit view insert format tools table",
    "plugins": "codesample link media image code fullscreen filehub table autolink advlist lists autoresize emoticons "
            "wordcount questionshortcode",
    "toolbar": [
        "bold italic underline strikethrough questionshortcode | forecolor blocks | subscript superscript | list "
        "bullist numlist blockquote | alignleft aligncenter alignright alignjustify | autolink link table ",
        "formatselect autolink | subscript superscript | outdent indent | filehub image media emoticons | ",
        "wordcount codesample fullscreen code"
    ],
    "image_advtab": False,
    "external_filemanager_path": "/filehub/select/",
    "filemanager_title": "Filemanager",
    "external_plugins": {
        "filehub": "/static/filehub/tinymce/plugin.js",
        "questionshortcode": "/static/admin/tinymce/questionshortcode/plugin.js",
    },
    "relative_urls": False,
    "remove_script_host": False,
    "toolbar_sticky": True,
    "image_dimensions": False,
    "noneditable_noneditable_class": 'alert',
    "min_height": 300,
    "license_key": "gpl",
    "content_css": [
        "/static/assets/css/tinymce.css"
    ],
    'setup': """function (editor) {
        editor.on('PastePreProcess', function(e) {
            const div = document.createElement("div");
            div.innerHTML = e.content;

            function cleanNode(node) {
                if (node.nodeType === 1) {
                    while (node.attributes.length > 0) {
                        node.removeAttribute(node.attributes[0].name);
                    }
                    for (let i = 0; i < node.childNodes.length; i++) {
                        cleanNode(node.childNodes[i]);
                    }
                } else if (node.nodeType === 8) {
                    node.parentNode.removeChild(node);
                }
            }

            cleanNode(div);
            e.content = div.innerHTML;
        });
    }"""
}

TINYMCE_EXTRA_MEDIA = {
    "css": {
        "all": [
            "/static/assets/css/tinymce.css",
        ]
    }
}