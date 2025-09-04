# Bip Shop E-Commerce API

This is a modern, asynchronous e-commerce backend API built with FastAPI and MongoDB. It provides a comprehensive set of features for managing products, users, authentication, shopping carts, and wishlists.

## Features

- **User Authentication**: Secure user signup, login, and logout using JWT (JSON Web Tokens) with access and refresh tokens.
- **Product Management**: Advanced search and filtering for products.
- **Shopping Cart**: Add, remove, view, and clear items in the user's cart.
- **Wishlist**: Add, remove, and view items in the user's wishlist.
- **Checkout Process**: Convert a cart into a persistent order.
- **Asynchronous**: Built with `async/await` syntax and `motor` for non-blocking database operations.

## Setup and Installation

Follow these steps to get the project running locally.

1.  **Clone the repository:**
    ```bash
    git clone <your-repository-url>
    cd bip-shop-api
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    # For Windows
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Create a `.env` file** in the root directory and add your MongoDB connection string:
    ```
    MONGO_URI="your_mongodb_atlas_connection_string"
    ```

## Running the Application

Use `uvicorn` to run the FastAPI server. The `--reload` flag will automatically restart the server when you make code changes.

```bash
uvicorn main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. You can access the interactive API documentation (Swagger UI) at `http://127.0.0.1:8000/docs`.