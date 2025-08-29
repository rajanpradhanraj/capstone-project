import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable } from 'rxjs';
import { AuthService } from './auth.service';

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  stock: number;
  category: string;
  image_url: string;
  created_at?: string;
  updated_at?: string;
}

export interface CartItem {
  cart_id: number;
  product_id: number;
  product_name: string;
  product_price: number;
  product_image: string;
  quantity: number;
  subtotal: number;
  available_stock: number;
}

export interface Cart {
  user_id: string;
  items: CartItem[];
  total_amount: number;
  item_count: number;
}

export interface Order {
  id: number;
  user_id: string;
  total_amount: number;
  status: string;
  created_at: string;
  updated_at: string;
  items: OrderItem[];
}

export interface OrderItem {
  id: number;
  order_id: number;
  product_id: number;
  product_name: string;
  price: number;
  quantity: number;
  subtotal: number;
}

@Injectable({
  providedIn: 'root'
})
export class ApiService {
  private baseUrl = 'http://localhost:5000/api';

  constructor(
    private http: HttpClient,
    private authService: AuthService
  ) {}

  private getHeaders(): HttpHeaders {
    const user = this.authService.getCurrentUser();
    return new HttpHeaders({
      'Content-Type': 'application/json',
      'X-User-ID': user?.id || 'user1',
      'X-User-Role': user?.role || 'user'
    });
  }

  // Authentication
  login(username: string, password: string): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/login`, { username, password });
  }

  register(username: string, password: string, role: string = 'user'): Observable<any> {
    return this.http.post(`${this.baseUrl}/auth/register`, { username, password, role });
  }

  getUsers(): Observable<any> {
    return this.http.get(`${this.baseUrl}/auth/users`);
  }

  // Products
  getProducts(category?: string, search?: string): Observable<Product[]> {
    let params = '';
    if (category) params += `category=${category}&`;
    if (search) params += `search=${search}&`;
    
    return this.http.get<Product[]>(`${this.baseUrl}/products?${params}`, {
      headers: this.getHeaders()
    });
  }

  getProduct(id: number): Observable<Product> {
    return this.http.get<Product>(`${this.baseUrl}/products/${id}`, {
      headers: this.getHeaders()
    });
  }

  createProduct(product: Partial<Product>): Observable<Product> {
    return this.http.post<Product>(`${this.baseUrl}/products`, product, {
      headers: this.getHeaders()
    });
  }

  updateProduct(id: number, product: Partial<Product>): Observable<Product> {
    return this.http.put<Product>(`${this.baseUrl}/products/${id}`, product, {
      headers: this.getHeaders()
    });
  }

  deleteProduct(id: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/products/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Cart
  getCart(): Observable<Cart> {
    return this.http.get<Cart>(`${this.baseUrl}/cart`, {
      headers: this.getHeaders()
    });
  }

  addToCart(productId: number, quantity: number = 1): Observable<any> {
    return this.http.post(`${this.baseUrl}/cart/add`, {
      product_id: productId,
      quantity
    }, {
      headers: this.getHeaders()
    });
  }

  updateCartItem(productId: number, quantity: number): Observable<any> {
    return this.http.put(`${this.baseUrl}/cart/update`, {
      product_id: productId,
      quantity
    }, {
      headers: this.getHeaders()
    });
  }

  removeFromCart(productId: number): Observable<any> {
    return this.http.delete(`${this.baseUrl}/cart/remove`, {
      headers: this.getHeaders(),
      body: { product_id: productId }
    });
  }

  clearCart(): Observable<any> {
    return this.http.delete(`${this.baseUrl}/cart/clear`, {
      headers: this.getHeaders()
    });
  }

  // Orders
  checkout(): Observable<any> {
    return this.http.post(`${this.baseUrl}/orders/checkout`, {}, {
      headers: this.getHeaders()
    });
  }

  getOrderHistory(): Observable<Order[]> {
    return this.http.get<Order[]>(`${this.baseUrl}/orders/history`, {
      headers: this.getHeaders()
    });
  }

  getOrder(id: number): Observable<Order> {
    return this.http.get<Order>(`${this.baseUrl}/orders/${id}`, {
      headers: this.getHeaders()
    });
  }

  // Admin
  getAllOrders(status?: string): Observable<Order[]> {
    const params = status ? `?status=${status}` : '';
    return this.http.get<Order[]>(`${this.baseUrl}/admin/orders${params}`, {
      headers: this.getHeaders()
    });
  }

  updateOrderStatus(orderId: number, status: string): Observable<Order> {
    return this.http.put<Order>(`${this.baseUrl}/admin/orders/${orderId}/status`, {
      status
    }, {
      headers: this.getHeaders()
    });
  }

  getDashboardData(): Observable<any> {
    return this.http.get(`${this.baseUrl}/admin/dashboard`, {
      headers: this.getHeaders()
    });
  }
}

