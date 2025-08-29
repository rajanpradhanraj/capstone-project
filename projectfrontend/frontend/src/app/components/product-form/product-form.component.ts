import { Component, Inject, OnInit } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';
import { ApiService, Product } from '../../services/api.service';

@Component({
  selector: 'app-product-form',
  templateUrl: './product-form.component.html',
  styleUrls: ['./product-form.component.scss']
})
export class ProductFormComponent implements OnInit {
  productForm: FormGroup;
  isEditMode = false;
  loading = false;

  categories = [
    'Electronics',
    'Clothing',
    'Home & Kitchen',
    'Sports',
    'Books',
    'Toys',
    'Beauty',
    'Automotive',
    'Health',
    'Furniture'
  ];

  constructor(
    private fb: FormBuilder,
    private apiService: ApiService,
    private snackBar: MatSnackBar,
    private dialogRef: MatDialogRef<ProductFormComponent>,
    @Inject(MAT_DIALOG_DATA) public data: Product | null
  ) {
    this.isEditMode = !!data;
    
    this.productForm = this.fb.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      description: [''],
      price: [0, [Validators.required, Validators.min(0.01)]],
      stock: [0, [Validators.required, Validators.min(0)]],
      category: ['', Validators.required],
      image_url: ['']
    });
  }

  ngOnInit(): void {
    if (this.isEditMode && this.data) {
      this.productForm.patchValue({
        name: this.data.name,
        description: this.data.description,
        price: this.data.price,
        stock: this.data.stock,
        category: this.data.category,
        image_url: this.data.image_url
      });
    }
  }

  onSubmit(): void {
    if (this.productForm.valid) {
      this.loading = true;
      const productData = this.productForm.value;

      const request = this.isEditMode 
        ? this.apiService.updateProduct(this.data!.id, productData)
        : this.apiService.createProduct(productData);

      request.subscribe({
        next: () => {
          this.loading = false;
          const message = this.isEditMode ? 'Product updated successfully' : 'Product created successfully';
          this.snackBar.open(message, 'Close', { duration: 3000 });
          this.dialogRef.close(true);
        },
        error: (error) => {
          this.loading = false;
          console.error('Error saving product:', error);
          this.snackBar.open('Error saving product', 'Close', { duration: 3000 });
        }
      });
    }
  }

  onCancel(): void {
    this.dialogRef.close(false);
  }

  getErrorMessage(fieldName: string): string {
    const field = this.productForm.get(fieldName);
    if (field?.hasError('required')) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} is required`;
    }
    if (field?.hasError('minlength')) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be at least ${field.errors?.['minlength']?.requiredLength} characters`;
    }
    if (field?.hasError('min')) {
      return `${fieldName.charAt(0).toUpperCase() + fieldName.slice(1)} must be greater than ${field.errors?.['min']?.min}`;
    }
    return '';
  }


  onImageError(event: Event): void {
    (event.target as HTMLImageElement).style.display = 'none';
  }

  onImageLoad(event: Event): void {
    (event.target as HTMLImageElement).style.display = 'block';
  }
}



