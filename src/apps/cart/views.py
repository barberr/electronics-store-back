from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.apps import apps
from .models import Cart, CartItem
from .serializers import (
    CartSerializer, CartItemSerializer,
    CartAddItemSerializer, CartUpdateItemSerializer
)


# Получаем модель из приложения products
def get_product_variant_model():
    return apps.get_model('products', 'ProductVariant')


class CartViewSet(viewsets.ViewSet):
    """Viewset для управления корзиной"""
    
    def get_cart(self, request):
        """Получить или создать корзину для пользователя/сессии"""
        if request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                user=request.user,
                defaults={'status': 'active'}
            )
            return cart
        else:
            session_key = request.session.session_key
            if not session_key:
                request.session.save()
                session_key = request.session.session_key
            
            cart, created = Cart.objects.get_or_create(
                session_key=session_key,
                defaults={'status': 'active'}
            )
            return cart
    
    def list(self, request):
        """Получить содержимое корзины"""
        cart = self.get_cart(request)
        serializer = CartSerializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Добавить товар в корзину"""
        cart = self.get_cart(request)
        serializer = CartAddItemSerializer(data=request.data)
        
        if serializer.is_valid():
            variant_id = serializer.validated_data['variant_id']
            quantity = serializer.validated_data['quantity']
            
            ProductVariant = get_product_variant_model()
            
            try:
                variant = ProductVariant.objects.get(id=variant_id)
                
                # Проверка доступности товара
                if quantity > variant.stock:
                    return Response(
                        {'error': f'Недостаточно товара на складе. Доступно: {variant.stock}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # Добавление или обновление элемента корзины
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    variant=variant,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    if cart_item.quantity > variant.stock:
                        return Response(
                            {'error': f'Недостаточно товара на складе. Доступно: {variant.stock}'},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    cart_item.save()
                
                cart_serializer = CartSerializer(cart)
                return Response(cart_serializer.data, status=status.HTTP_201_CREATED)
            
            except ProductVariant.DoesNotExist:
                return Response(
                    {'error': 'Вариант товара не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def update_item(self, request):
        """Обновить количество товара в корзине"""
        cart = self.get_cart(request)
        item_id = request.data.get('item_id')
        serializer = CartUpdateItemSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                cart_item = CartItem.objects.get(id=item_id, cart=cart)
                quantity = serializer.validated_data['quantity']
                
                # Проверка доступности товара
                if quantity > cart_item.variant.stock:
                    return Response(
                        {'error': f'Недостаточно товара на складе. Доступно: {cart_item.variant.stock}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                cart_item.quantity = quantity
                cart_item.save()
                
                cart_serializer = CartSerializer(cart)
                return Response(cart_serializer.data)
            
            except CartItem.DoesNotExist:
                return Response(
                    {'error': 'Элемент корзины не найден'},
                    status=status.HTTP_404_NOT_FOUND
                )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Удалить товар из корзины"""
        cart = self.get_cart(request)
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            
            cart_serializer = CartSerializer(cart)
            return Response(cart_serializer.data)
        
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Элемент корзины не найден'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Очистить корзину"""
        cart = self.get_cart(request)
        cart.items.all().delete()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)
    
    @action(detail=False, methods=['post'])
    def checkout(self, request):
        """Оформить заказ из корзины"""
        cart = self.get_cart(request)
        
        # Проверка наличия товаров в корзине
        if not cart.items.exists():
            return Response(
                {'error': 'Корзина пуста'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Логика создания заказа (будет реализована позже)
        cart_serializer = CartSerializer(cart)
        return Response({
            'cart': cart_serializer.data,
            'message': 'Переход к оформлению заказа',
            'next_step': '/checkout'
        })