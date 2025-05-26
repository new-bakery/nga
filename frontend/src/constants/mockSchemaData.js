export const MOCK_SCHEMA_DATA = {
  excel: {
    tables: [
      {
        id: 'sales',
        name: 'Sales',
        columns: [
          { id: 'sale_id', name: 'Sale ID', type: 'INTEGER', annotation: 'Unique identifier for each sale' },
          { id: 'date', name: 'Date', type: 'DATE', annotation: 'Date of sale' },
          { id: 'customer_id', name: 'Customer ID', type: 'INTEGER', annotation: 'Reference to Customers table' },
          { id: 'product_id', name: 'Product ID', type: 'INTEGER', annotation: 'Reference to Products table' },
          { id: 'quantity', name: 'Quantity', type: 'INTEGER', annotation: 'Number of units sold' },
          { id: 'amount', name: 'Amount', type: 'DECIMAL', annotation: 'Total sale amount' }
        ]
      },
      {
        id: 'customers',
        name: 'Customers',
        columns: [
          { id: 'customer_id', name: 'Customer ID', type: 'INTEGER', annotation: 'Primary key' },
          { id: 'name', name: 'Name', type: 'VARCHAR', annotation: 'Customer full name' },
          { id: 'email', name: 'Email', type: 'VARCHAR', annotation: 'Contact email' },
          { id: 'region', name: 'Region', type: 'VARCHAR', annotation: 'Geographic region' }
        ]
      },
      {
        id: 'products',
        name: 'Products',
        columns: [
          { id: 'product_id', name: 'Product ID', type: 'INTEGER', annotation: 'Primary key' },
          { id: 'name', name: 'Name', type: 'VARCHAR', annotation: 'Product name' },
          { id: 'category', name: 'Category', type: 'VARCHAR', annotation: 'Product category' },
          { id: 'price', name: 'Price', type: 'DECIMAL', annotation: 'Unit price' }
        ]
      }
    ],
    relationships: [
      {
        id: 'sales_customers',
        name: 'Sales to Customers',
        from: {
          tableId: 'sales',
          columnId: 'customer_id'
        },
        to: {
          tableId: 'customers',
          columnId: 'customer_id'
        }
      },
      {
        id: 'sales_products',
        name: 'Sales to Products',
        from: {
          tableId: 'sales',
          columnId: 'product_id'
        },
        to: {
          tableId: 'products',
          columnId: 'product_id'
        }
      }
    ]
  },
  mysql: {
    tables: [
      {
        id: 'orders',
        name: 'Orders',
        columns: [
          { id: 'order_id', name: 'Order ID', type: 'INTEGER', annotation: 'Primary key' },
          { id: 'user_id', name: 'User ID', type: 'INTEGER', annotation: 'Reference to Users table' },
          { id: 'order_date', name: 'Order Date', type: 'DATETIME', annotation: 'When order was placed' },
          { id: 'status', name: 'Status', type: 'VARCHAR', annotation: 'Order status' },
          { id: 'total', name: 'Total', type: 'DECIMAL', annotation: 'Order total amount' }
        ]
      },
      {
        id: 'users',
        name: 'Users',
        columns: [
          { id: 'user_id', name: 'User ID', type: 'INTEGER', annotation: 'Primary key' },
          { id: 'username', name: 'Username', type: 'VARCHAR', annotation: 'User login name' },
          { id: 'email', name: 'Email', type: 'VARCHAR', annotation: 'User email address' },
          { id: 'created_at', name: 'Created At', type: 'DATETIME', annotation: 'Account creation date' }
        ]
      }
    ],
    relationships: [
      {
        id: 'orders_users',
        name: 'Orders to Users',
        from: {
          tableId: 'orders',
          columnId: 'user_id'
        },
        to: {
          tableId: 'users',
          columnId: 'user_id'
        }
      }
    ]
  }
}; 