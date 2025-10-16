import os
import stripe
from typing import Dict, Any, Optional, List
from datetime import datetime

# Initialize Stripe with API key
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

def get_stripe_client():
    """Get Stripe client instance"""
    return stripe


def create_customer(*, email: str, name: str) -> Dict[str, Any]:
    """Create a Stripe customer"""
    return stripe.Customer.create(
        email=email,
        name=name,
        metadata={"source": "creatorpulse"}
    )


def create_subscription(*, customer_id: str, price_id: str, trial_days: int = 14) -> Dict[str, Any]:
    """Create a Stripe subscription"""
    return stripe.Subscription.create(
        customer=customer_id,
        items=[{"price": price_id}],
        trial_period_days=trial_days,
        expand=["latest_invoice.payment_intent"]
    )


def cancel_subscription(*, subscription_id: str) -> Dict[str, Any]:
    """Cancel a Stripe subscription"""
    return stripe.Subscription.delete(subscription_id)


def get_subscription(*, subscription_id: str) -> Dict[str, Any]:
    """Get subscription details from Stripe"""
    return stripe.Subscription.retrieve(subscription_id)


def create_checkout_session(*, customer_id: str, price_id: str, success_url: str, cancel_url: str) -> Dict[str, Any]:
    """Create a Stripe Checkout session"""
    return stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{
            "price": price_id,
            "quantity": 1,
        }],
        mode="subscription",
        success_url=success_url,
        cancel_url=cancel_url,
        allow_promotion_codes=True,
        subscription_data={
            "trial_period_days": 14,
        }
    )


def create_portal_session(*, customer_id: str, return_url: str) -> Dict[str, Any]:
    """Create a Stripe Customer Portal session"""
    return stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=return_url,
    )


def list_products() -> List[Dict[str, Any]]:
    """List all Stripe products"""
    return stripe.Product.list(active=True).data


def list_prices() -> List[Dict[str, Any]]:
    """List all Stripe prices"""
    return stripe.Price.list(active=True).data


def get_price(*, price_id: str) -> Dict[str, Any]:
    """Get price details from Stripe"""
    return stripe.Price.retrieve(price_id)


def construct_webhook_event(*, payload: bytes, sig_header: str) -> Dict[str, Any]:
    """Verify and construct webhook event"""
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        raise ValueError("STRIPE_WEBHOOK_SECRET not set")
    
    return stripe.Webhook.construct_event(
        payload, sig_header, webhook_secret
    )


def format_price(cents: int) -> str:
    """Format price in cents to currency string"""
    return f"${cents / 100:.2f}"


def get_plan_features(plan_id: str) -> Dict[str, Any]:
    """Get features for a subscription plan"""
    features_map = {
        "free": {
            "workspaces": 1,
            "team_members": 1,
            "sources": 5,
            "newsletters_per_month": 10,
            "analytics": False,
            "priority_support": False,
            "white_label": False
        },
        "pro": {
            "workspaces": 5,
            "team_members": 10,
            "sources": 50,
            "newsletters_per_month": 100,
            "analytics": True,
            "priority_support": True,
            "white_label": False
        },
        "agency": {
            "workspaces": 50,
            "team_members": 100,
            "sources": 500,
            "newsletters_per_month": 1000,
            "analytics": True,
            "priority_support": True,
            "white_label": True
        }
    }
    return features_map.get(plan_id, features_map["free"])


def get_plan_limits(plan_id: str) -> Dict[str, Any]:
    """Get limits for a subscription plan"""
    limits_map = {
        "free": {
            "max_workspaces": 1,
            "max_team_members": 1,
            "max_sources": 5,
            "max_newsletters_per_month": 10
        },
        "pro": {
            "max_workspaces": 5,
            "max_team_members": 10,
            "max_sources": 50,
            "max_newsletters_per_month": 100
        },
        "agency": {
            "max_workspaces": 50,
            "max_team_members": 100,
            "max_sources": 500,
            "max_newsletters_per_month": 1000
        }
    }
    return limits_map.get(plan_id, limits_map["free"])
