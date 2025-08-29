import { Component, EventEmitter, Input, Output } from '@angular/core';

export interface Product {
  id: number | string;
  name: string;
  price: number;
  description?: string;
  imageUrl?: string;
}

@Component({
  selector: 'app-product-card',
  templateUrl: './product-card.component.html',
  styleUrls: ['./product-card.component.scss']
})
export class ProductCardComponent {
  @Input() product!: Product;

  @Output() addToCart = new EventEmitter<Product>();
  @Output() view = new EventEmitter<Product>();
}
