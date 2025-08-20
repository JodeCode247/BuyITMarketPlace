# 🛒 BuyIt: An Open Marketplace Web Application

Welcome to the BuyIt repository!
This project is an evolving online marketplace platform where users can browse, buy, and sell products.
It’s built with modern web technologies (Django + GraphQL + Vanilla JS) and designed for scalability.

🎯 Project Overview

The BuyIt Marketplace is a dynamic e-commerce platform designed to connect buyers and sellers.
Users can explore products, manage listings, and make secure purchases with a smooth experience.

The application is modular, scalable, and cleanly structured.
It features secure authentication, product management, media uploads, and checkout workflows.

✨ Key Features

🔐 User Authentication – Secure registration and login

🛍️ Product Listings – Create, view, edit, and delete products with details & images

🔍 Search & Filter – Find products by category, name, or criteria

🛒 Shopping Cart & Checkout – Add items, manage cart, and checkout securely

📱 Responsive UI – Works across desktop, tablet, and mobile

💳 Payment Integration – Supports Paystack for secure transactions

☁️ Media Uploads – Uses Cloudinary for optimized image storage

# 🛠️ Tech Stack
Backend

Django – Web framework for robust development

Frontend

HTML, CSS, JavaScript – Core web technologies

jQuery – Lightweight DOM manipulation & async calls

Select2 – For advanced dropdown UI

Database

PostgreSQL (recommended) – Can also run on SQLite locally

Third-Party Services

Cloudinary – Media upload and optimization

Paystack – Secure payment gateway

⚙️ Core Functionality
📷 Image Uploads with Cloudinary

When users upload product images, they’re stored in Cloudinary.
This ensures faster delivery, optimization, and reduced server load.

🛒 Cart Updates with JavaScript

The cart icon updates in real-time without page reloads.
This is done via async requests (AJAX) to the backend, giving instant user feedback.

💳 Payments with Paystack

Checkout is powered by Paystack.
When a payment is completed, the backend processes the order and updates status securely.

🚀 Installation & Setup
Prerequisites

Python 3.x

pip

Git

Steps

1️⃣ Clone the Repository

git clone https://github.com/JodeCode247/BuyITMarketPlace.git
cd BuyITMarketPlace


2️⃣ Create a Virtual Environment

python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate


3️⃣ Install Dependencies

pip install -r requirements.txt


4️⃣ Setup Database
Edit settings.py for DB configs, then run:

python manage.py makemigrations


python manage.py migrate


5️⃣ Create Superuser

python manage.py createsuperuser


6️⃣ Run Development Server

python manage.py runserver


Now visit 👉 http://localhost:8000
