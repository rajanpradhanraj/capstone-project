import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService, Product } from '../../services/api.service';
import { CartService } from '../../services/cart.service';

@Component({
  selector: 'app-product-list',
  templateUrl: './product-list.component.html',
  styleUrls: ['./product-list.component.scss']
})
export class ProductListComponent implements OnInit {
  products: Product[] = [];
  filteredProducts: Product[] = [];
  loading = true;
  searchTerm = '';
  selectedCategory = '';
  categories: string[] = [];

  constructor(
    private apiService: ApiService,
    private cartService: CartService,
    private snackBar: MatSnackBar,
    private route: ActivatedRoute,
    private router: Router
  ) {}

  ngOnInit(): void {
    // Listen for query parameter changes
    this.route.queryParams.subscribe(params => {
      if (params['category']) {
        this.selectedCategory = params['category'];
        this.filterProducts();
      }
    });
    
    this.loadProducts();
  }

  loadProducts(): void {
    this.loading = true;
    this.apiService.getProducts().subscribe({
      next: (products) => {
        this.products = products;
        this.filteredProducts = products;
        this.extractCategories();
        this.loading = false;
      },
      error: (error) => {
        console.error('Error loading products:', error);
        this.snackBar.open('Error loading products', 'Close', { duration: 3000 });
        this.loading = false;
      }
    });
  }

  extractCategories(): void {
    const categorySet = new Set(this.products.map(p => p.category).filter(c => c));
    this.categories = Array.from(categorySet);
  }

  onSearch(): void {
    this.filterProducts();
  }

  onCategoryChange(): void {
    this.filterProducts();
    // Update URL with category parameter
    if (this.selectedCategory) {
      this.router.navigate(['/user/products'], { 
        queryParams: { category: this.selectedCategory } 
      });
    } else {
      this.router.navigate(['/user/products']);
    }
  }

  filterProducts(): void {
    let filtered = [...this.products];

    if (this.searchTerm) {
      filtered = filtered.filter(product =>
        product.name.toLowerCase().includes(this.searchTerm.toLowerCase()) ||
        product.description.toLowerCase().includes(this.searchTerm.toLowerCase())
      );
    }

    if (this.selectedCategory) {
      filtered = filtered.filter(product => product.category === this.selectedCategory);
    }

    this.filteredProducts = filtered;
  }

  addToCart(product: Product): void {
    if (product.stock <= 0) {
      this.snackBar.open('Product is out of stock', 'Close', { duration: 3000 });
      return;
    }

    this.cartService.addToCart(product.id, 1).subscribe({
      next: () => {
        this.snackBar.open(`${product.name} added to cart`, 'Close', { duration: 2000 });
      },
      error: (error) => {
        console.error('Error adding to cart:', error);
        this.snackBar.open('Error adding product to cart', 'Close', { duration: 3000 });
      }
    });
  }

  clearFilters(): void {
    this.searchTerm = '';
    this.selectedCategory = '';
    this.filteredProducts = [...this.products];
  }
}

