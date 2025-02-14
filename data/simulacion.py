# generate_sample_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_sales_data(n_rows=1000):
    # Fechas
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    dates = pd.date_range(start=start_date, end=end_date, periods=n_rows)
    
    # Productos (categorías limitadas para mejor testing)
    products = ['Laptop', 'Smartphone', 'Tablet', 'Monitor', 'Keyboard']
    product_prices = {
        'Laptop': (800, 1500),
        'Smartphone': (400, 1000),
        'Tablet': (200, 600),
        'Monitor': (150, 400),
        'Keyboard': (20, 100)
    }
    
    # Vendedores
    sellers = ['Juan', 'Maria', 'Carlos', 'Ana', 'Pedro']
    
    # Clientes (generamos IDs y nombres)
    n_customers = 50  # número limitado de clientes para ver patrones
    customer_ids = range(1001, 1001 + n_customers)
    customer_names = [f'Cliente_{i}' for i in customer_ids]
    
    data = {
        'fecha_venta': dates,
        'producto': [random.choice(products) for _ in range(n_rows)],
        'vendedor': [random.choice(sellers) for _ in range(n_rows)],
        'cliente_id': [random.choice(customer_ids) for _ in range(n_rows)],
        'cliente_nombre': [f'Cliente_{i}' for i in [random.choice(customer_ids) for _ in range(n_rows)]],
        'cantidad': np.random.randint(1, 5, size=n_rows)
    }
    
    # Calculamos precio basado en producto
    data['precio_unitario'] = [random.uniform(*product_prices[p]) for p in data['producto']]
    data['total_venta'] = [p * q for p, q in zip(data['precio_unitario'], data['cantidad'])]
    
    df = pd.DataFrame(data)
    
    # Redondear valores numéricos
    df['precio_unitario'] = df['precio_unitario'].round(2)
    df['total_venta'] = df['total_venta'].round(2)
    
    return df

if __name__ == "__main__":
    # Generar datos
    df = generate_sales_data()
    
    # Guardar como CSV
    df.to_csv('sample_sales_data.csv', index=False)
    
    # Imprimir información del dataset
    print("\nDataset generado exitosamente!")
    print("\nEstructura del dataset:")
    print(df.info())
    print("\nPrimeras 5 filas:")
    print(df.head())