-- Postgres + PostGIS schema for Grocery Recommendations
-- This script is designed for psql. It will:
-- 1) Create database `grocery_db` if missing (psql-specific) and connect to it
-- 2) Enable PostGIS
-- 3) Create tables, constraints, and indexes

-- 1) Create database if it doesn't exist (psql-only; requires \gexec)
SELECT 'CREATE DATABASE grocery_db'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'grocery_db')\gexec

-- 2) Connect to the target database (psql meta-command)
\connect grocery_db

-- 3) Enable PostGIS
CREATE EXTENSION IF NOT EXISTS postgis;

-- 4) Tables

-- Users
CREATE TABLE IF NOT EXISTS users (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  email VARCHAR(255) NOT NULL UNIQUE,
  name VARCHAR(255),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- Categories
CREATE TABLE IF NOT EXISTS categories (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(255) NOT NULL UNIQUE,
  slug VARCHAR(255)
);
-- Unique slug when provided (allow multiple NULLs)
CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_slug ON categories(slug) WHERE slug IS NOT NULL;

-- Shops with PostGIS geography Point (lon,lat in SRID 4326)
CREATE TABLE IF NOT EXISTS shops (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  address VARCHAR(512),
  location geography(POINT,4326) NOT NULL
);

-- Products, with analytics fields
CREATE TABLE IF NOT EXISTS products (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  shop_id INTEGER NOT NULL REFERENCES shops(id) ON DELETE CASCADE,
  daily_views INTEGER NOT NULL DEFAULT 0,
  weekly_sales INTEGER NOT NULL DEFAULT 0,
  last_purchased_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- Event tracking for personalization
CREATE TABLE IF NOT EXISTS product_view_events (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS purchase_events (
  id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
  quantity INTEGER NOT NULL DEFAULT 1,
  price_at_purchase NUMERIC(10,2),
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 5) Indexes for performance
-- Geospatial index for nearby shop queries
CREATE INDEX IF NOT EXISTS idx_shops_location_gix ON shops USING GIST (location);
-- Product lookups
CREATE INDEX IF NOT EXISTS idx_products_shop_id ON products(shop_id);
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
-- Event time-series + lookups
CREATE INDEX IF NOT EXISTS idx_pve_user_id_created_at ON product_view_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pe_user_id_created_at ON purchase_events(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_pve_product_id ON product_view_events(product_id);
CREATE INDEX IF NOT EXISTS idx_pe_product_id ON purchase_events(product_id);

-- 6) Helpful notes
-- Insert a shop (longitude, latitude order):
-- INSERT INTO shops (name, address, location)
-- VALUES (
--   'City Mart', 'Downtown',
--   ST_SetSRID(ST_MakePoint(67.0011, 24.8607), 4326)::geography
-- );
