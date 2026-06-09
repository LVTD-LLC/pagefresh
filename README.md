<p align="center">
  <img src="#" width="230" alt="PageFresh Logo">
</p>

<!--  -->
<div align="center">
  <b>PageFresh</b>
  <b>Scheduled page review reminders for every sitemap.</b>
</div>

***

## Overview

PageFresh imports sitemap pages, tracks review status, and sends scheduled email digests so website owners and agencies can keep content current.

***

## TOC

- [Overview](#overview)
- [TOC](#toc)
- [Deployment](#deployment)
  - [Render](#render)
  - [Docker Compose](#docker-compose)
  - [Pure Python / Django deployment](#pure-python--django-deployment)
  - [Custom Deployment on Caprover](#custom-deployment-on-caprover)
- [Local Development](#local-development)
- [Stripe Setup](#stripe-setup)

***

## Deployment

### Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/rasulkireev/cleanapp)

**Note:** This should work out of the box with Render's free tier for light PageFresh usage. Here's what you need to know about the limitations:

- **Worker Service Limitation**: The worker service is not a dedicated worker type (those are only available on paid plans). For the free tier, I had to use a web service through a small hack, but it works fine for small review queues.

- **Memory Constraints**: The free web service has a 512 MB RAM limit, which can cause issues with **automated background tasks only**. Large sitemaps and busy digest schedules may need a paid instance.

- **Manual Tasks Work Fine**: Reviewing pages in the dashboard typically uses the web service and should be reliable because it is one request at a time.

- **Upgrade Recommendation**: If you do upgrade to a paid plan, use the actual worker service instead of the web service workaround for better automated task reliability.

**Reality Check**: PageFresh should be usable on the free tier for a small number of sites. Automated sitemap imports and email digests may occasionally fail on heavy workloads due to memory constraints.

If you know of any other services like Render that allow deployment via a button and provide free Redis, Postgres, and web services, please let me know in the [Issues](https://github.com/rasulkireev/cleanapp/issues) section. I can try to create deployments for those. Bear in mind that free services are usually not large enough to run this application reliably.


### Docker Compose

This should also be pretty streamlined. On your server you can create a folder in which you will have 2 files:

1. `.env`

Copy the contents of `.env.example` into `.env` and update all the necessary values.

2. `docker-compose.yml`

Copy the contents of `docker-compose-prod.yml` into `docker-compose.yml` and run the suggested command from the top of the `docker-compose-prod.yml` file.

How you are going to expose the backend container is up to you. Existing compose examples may still use the legacy `cleanapp` project name, for example `http://cleanapp-backend-1:80` as `UPSTREAM_HTTP_ADDRESS`.


### Pure Python / Django deployment

Not recommended due to not being too safe for production and not being tested by me.

If you are not into Docker or Render and just wanto to run this via regular commands you will need to have 5 processes running:
- `python manage.py collectstatic --noinput && python manage.py migrate && gunicorn ${PROJECT_NAME}.wsgi:application --bind 0.0.0.0:80 --workers 3 --threads 2`
- `python manage.py qcluster`
- `npm install && npm run start`
- `postgres`
- `redis`

You'd still need to make sure .env has correct values.

### Custom Deployment on Caprover

1. Create 4 apps on CapRover.
  - `cleanapp`
  - `cleanapp-workers`
  - `cleanapp-postgres`
  - `cleanapp-redis`

2. Create a new CapRover app token for:
   - `cleanapp`
   - `cleanapp-workers`

3. Add Environment Variables to those same apps from `.env`.

4. Create a new GitHub Actions secret with the following:
   - `CAPROVER_SERVER`
   - `CAPROVER_APP_TOKEN`
   - `WORKERS_APP_TOKEN`
   - `REGISTRY_TOKEN`

5. Then just push main branch.

6. Github Workflow in this repo should take care of the rest.

## Local Development

1. Update the name of the `.env.example` to `.env` and update relevant variables.
2. Run `poetry export -f requirements.txt --output requirements.txt --without-hashes`
3. Run `poetry run python manage.py makemigrations`
4. Run `make serve`
5. Run `make restart-worker` just in case, it sometimes has troubles connecting to REDIS on first deployment.

## Stripe Setup

This app uses Stripe Checkout for purchases and the Billing Portal for subscription management.

### Configure Stripe

- Set the following in `.env`:
  - `STRIPE_SECRET_KEY`
  - `STRIPE_PUBLISHABLE_KEY` (optional, only needed for client-side Stripe.js)
  - `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_ID_MONTHLY`
  - `STRIPE_PRICE_ID_YEARLY`
  - `WEBHOOK_UUID` (optional, used to gate webhook URLs)
- Enable the Billing Portal in the Stripe Dashboard and allow subscription updates and cancellations.
- Create a webhook endpoint in the Stripe Dashboard:
  - URL: `https://<your-domain>/stripe/webhook/<WEBHOOK_UUID>/` (or `/stripe/webhook/` if no UUID)
  - Events: `customer.subscription.created`, `customer.subscription.updated`, `customer.subscription.deleted`, `checkout.session.completed`

### Test Webhooks Locally

- Use the Stripe CLI container (see `docker-compose-local.yml`) to forward webhooks:
  - `docker compose -f docker-compose-local.yml run --rm stripe listen --forward-to http://backend:8000/stripe/webhook/${WEBHOOK_UUID}/`
- Trigger a test event:
  - `docker compose -f docker-compose-local.yml run --rm stripe trigger customer.subscription.created`
