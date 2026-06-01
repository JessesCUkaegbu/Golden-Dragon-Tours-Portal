# Tixora — Event Ticketing Platform

A full-featured SaaS ticketing platform built with **Django, Bootstrap, and JavaScript**, designed for both ticket buyers and event organisers across subscription tiers.

---

## What is Tixora?

Tixora is a subscription-based digital ticketing platform where users can discover events, purchase tickets, and receive barcoded PDF tickets — while organisers can publish events, manage capacity, and track attendee ticket status from a dedicated Event Studio dashboard.

---

## Features

### For Ticket Buyers
- User registration, login, and account management
- Browse and discover active events
- Purchase digital tickets with barcode generation
- Receive ticket confirmation emails with PDF attachment
- View full ticket history and download PDF tickets from the dashboard
- Monthly ticket limits based on subscription plan

### For Event Organisers
- Dedicated Event Studio dashboard
- Create, edit, and delete events with image uploads
- Set ticket price, capacity, and payment phone number
- View all sold tickets per event
- Confirm or cancel individual attendee tickets
- Active event limits based on subscription plan

### Platform
- Subscription tiers: Free, Standard, Premium
- Stripe-powered subscription checkout and management
- Cloudinary cloud storage for ticket barcodes and event images
- Transactional email via Zoho Mail (welcome + ticket confirmation)
- Custom-branded PDF ticket with embedded barcode
- Secure HTTPS-enforced deployment on Railway

---

## Subscription Tiers

| Feature | Free | Standard | Premium |
|---|---|---|---|
| Tickets per month (buyer) | 10 | 50 | Unlimited |
| Active events (organiser) | 1 | 10 | Unlimited |
| Max attendees per event | 10 | 500 | Unlimited |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 6.0.3 |
| Frontend | HTML5, CSS3, Bootstrap 5.3.3, JavaScript |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Payments | Stripe |
| Cloud Storage | Cloudinary |
| Email | Zoho Mail (SMTP) |
| Barcode / PDF | python-barcode, Pillow |
| Admin UI | Django Jazzmin |
| Deployment | Railway + Gunicorn + WhiteNoise |

---

## Project Workflow

1. User registers or logs in
2. User browses events or initiates a ticket purchase from the dashboard
3. Ticket form is submitted — reference code is generated (`TKT-XXXXXXXXXX`)
4. Barcode is generated and uploaded to Cloudinary
5. Confirmation email sent with PDF ticket attached
6. Organiser reviews tickets in Event Studio and confirms or cancels attendees

---

## Deployment

Live at: [tixora.org](https://tixora.org)

Deployed on Railway with PostgreSQL, environment-managed via `.env`. Static files served by WhiteNoise. Media and generated assets stored on Cloudinary.
