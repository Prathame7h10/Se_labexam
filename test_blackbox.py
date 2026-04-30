"""
=============================================================
 BLACK BOX TESTING – Online Food Ordering System
 Use Case  : Place Order
 Techniques: Equivalence Class Partitioning (ECP)
             Boundary Value Analysis (BVA)
 Course    : Software Engineering (R5IT2009T)
 Institute : VJTI Mumbai | IV B.Tech Computer Engg
=============================================================
 Preconditions:
   - Customer is registered & logged in
   - Restaurant is active / open
   - Payment gateway is reachable
   - Cart has at least 1 item

 Postconditions:
   - Order confirmed/rejected with proper status
   - Payment processed or refunded
   - Notification sent to customer
=============================================================
 HOW TO RUN:
   python test_blackbox.py          <- runs all 15 test cases
   python -m unittest test_blackbox <- same via unittest runner
=============================================================
"""

import unittest
import sys

# ── Import the system under test ──────────────────────────
from place_order import (
    Cart, CartItem, Restaurant, PaymentGateway,
    OrderController,
    ValidationException, EmptyCartException,
    MaxLimitException, InvalidPaymentException,
    RestaurantClosedException, PaymentException,
)

# ─────────────────────────────────────────────────────────
# Helper: build a Cart quickly
# ─────────────────────────────────────────────────────────
def make_cart(*items):
    """items = list of (name, qty, price) tuples"""
    c = Cart()
    for name, qty, price in items:
        c.add_item(CartItem(name, qty, price))
    return c


# ─────────────────────────────────────────────────────────
# BLACK BOX TEST CLASS
# ─────────────────────────────────────────────────────────
class BlackBoxTests(unittest.TestCase):

    def setUp(self):
        """Runs before every test – fresh gateway + controller."""
        self.gw         = PaymentGateway()
        self.controller = OrderController(self.gw)
        self.rest_open  = Restaurant("R01", "Spice Garden", Restaurant.OPEN)
        self.rest_closed= Restaurant("R02", "Night Bites",  Restaurant.CLOSED)

    # ─────────────────────────────────────────────────────
    # ECP – VALID CLASS
    # ─────────────────────────────────────────────────────

    def test_BB_TC_01_valid_order_UPI(self):
        """
        TC ID      : BB-TC-01
        Technique  : ECP – Valid Class
        Description: All inputs in valid equivalence class.
                     Registered customer, non-empty cart, UPI payment, OPEN restaurant.
        Input      : custId=C001, items=[Pizza×2 ₹360, Burger×1 ₹120],
                     payMode=UPI, restaurant=OPEN, total=₹480
        Expected   : Order placed successfully. OrderID generated. Confirmation sent.
        """
        cart   = make_cart(("Pizza", 2, 180.0), ("Burger", 1, 120.0))
        result = self.controller.placeOrder("C001", cart, "UPI", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertIn("order_id",  result)
        self.assertIn("tracking",  result)
        self.assertEqual(result["total"], 480.0)
        print("\n[BB-TC-01] PASS | Valid UPI order | Total=₹480 | "
              f"OrderID={result['order_id']}")

    def test_BB_TC_11_valid_order_Wallet(self):
        """
        TC ID      : BB-TC-11
        Technique  : ECP – Valid Class
        Description: Valid order using Wallet payment mode.
        Input      : custId=C010, items=[Burger×3 ₹450],
                     payMode=Wallet, restaurant=OPEN
        Expected   : Order placed successfully. Payment debited from wallet.
        """
        cart   = make_cart(("Burger", 3, 150.0))
        result = self.controller.placeOrder("C010", cart, "Wallet", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 450.0)
        print(f"\n[BB-TC-11] PASS | Valid Wallet order | Total=₹450 | "
              f"OrderID={result['order_id']}")

    def test_BB_TC_12_valid_order_Card(self):
        """
        TC ID      : BB-TC-12
        Technique  : ECP – Valid Class
        Description: Valid order using Card payment mode.
        Input      : custId=C011, items=[Thali×1 ₹220],
                     payMode=Card, restaurant=OPEN
        Expected   : Order placed successfully. Card payment processed.
        """
        cart   = make_cart(("Thali", 1, 220.0))
        result = self.controller.placeOrder("C011", cart, "Card", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 220.0)
        print(f"\n[BB-TC-12] PASS | Valid Card order | Total=₹220 | "
              f"OrderID={result['order_id']}")

    # ─────────────────────────────────────────────────────
    # ECP – INVALID CLASS
    # ─────────────────────────────────────────────────────

    def test_BB_TC_02_null_customer_id(self):
        """
        TC ID      : BB-TC-02
        Technique  : ECP – Invalid Class
        Description: Customer ID is NULL. Tests S1 null-check validation.
        Input      : custId=NULL, items=[Pizza×1 ₹180],
                     payMode=Card, restaurant=OPEN
        Expected   : ValidationException – 'Customer ID cannot be null.'
        """
        cart = make_cart(("Pizza", 1, 180.0))
        with self.assertRaises(ValidationException) as ctx:
            self.controller.placeOrder(None, cart, "Card", self.rest_open)
        self.assertIn("null", str(ctx.exception).lower())
        print(f"\n[BB-TC-02] PASS | NULL custId blocked | {ctx.exception}")

    def test_BB_TC_03_empty_cart(self):
        """
        TC ID      : BB-TC-03
        Technique  : ECP – Invalid Class
        Description: Cart has zero items. Tests S2 empty-cart guard.
        Input      : custId=C002, items=[],
                     payMode=Wallet, restaurant=OPEN
        Expected   : EmptyCartException – 'Cart cannot be empty.'
        """
        cart = Cart()   # empty
        with self.assertRaises(EmptyCartException) as ctx:
            self.controller.placeOrder("C002", cart, "Wallet", self.rest_open)
        self.assertIn("empty", str(ctx.exception).lower())
        print(f"\n[BB-TC-03] PASS | Empty cart blocked | {ctx.exception}")

    def test_BB_TC_04_invalid_payment_mode(self):
        """
        TC ID      : BB-TC-04
        Technique  : ECP – Invalid Class
        Description: Payment mode 'Bitcoin' is unsupported. Tests S4 validation.
        Input      : custId=C003, items=[Pasta×1 ₹250],
                     payMode=Bitcoin, restaurant=OPEN
        Expected   : InvalidPaymentException – 'Invalid payment method.'
        """
        cart = make_cart(("Pasta", 1, 250.0))
        with self.assertRaises(InvalidPaymentException) as ctx:
            self.controller.placeOrder("C003", cart, "Bitcoin", self.rest_open)
        self.assertIn("invalid", str(ctx.exception).lower())
        print(f"\n[BB-TC-04] PASS | Invalid payMode blocked | {ctx.exception}")

    def test_BB_TC_05_restaurant_closed(self):
        """
        TC ID      : BB-TC-05
        Technique  : ECP – Invalid Class
        Description: Restaurant is CLOSED. Tests S5 open-status guard.
        Input      : custId=C004, items=[Sandwich×2 ₹300],
                     payMode=UPI, restaurant=CLOSED
        Expected   : RestaurantClosedException – 'Restaurant is currently closed.'
        """
        cart = make_cart(("Sandwich", 2, 150.0))
        with self.assertRaises(RestaurantClosedException) as ctx:
            self.controller.placeOrder("C004", cart, "UPI", self.rest_closed)
        self.assertIn("closed", str(ctx.exception).lower())
        print(f"\n[BB-TC-05] PASS | Closed restaurant blocked | {ctx.exception}")

    def test_BB_TC_13_payment_gateway_failure(self):
        """
        TC ID      : BB-TC-13
        Technique  : ECP – Invalid Class
        Description: Payment gateway is DOWN (timeout). Tests S6 failure path.
        Input      : custId=C012, items=[Dosa×2 ₹160],
                     payMode=UPI, gateway=TIMEOUT, restaurant=OPEN
        Expected   : PaymentException – 'Payment failed. Please retry.'
        """
        self.gw.simulate_failure()          # bring gateway down
        cart = make_cart(("Dosa", 2, 80.0))
        with self.assertRaises(PaymentException) as ctx:
            self.controller.placeOrder("C012", cart, "UPI", self.rest_open)
        self.assertIn("failed", str(ctx.exception).lower())
        print(f"\n[BB-TC-13] PASS | Gateway failure handled | {ctx.exception}")

    def test_BB_TC_14_restaurant_rejects_order(self):
        """
        TC ID      : BB-TC-14
        Technique  : ECP – Invalid Class
        Description: Restaurant accepts the request but then rejects the order.
                     Refund must be initiated via S7 rejection path.
        Input      : custId=C013, items=[Biryani×1 ₹350],
                     payMode=UPI, restaurant=OPEN (rejects internally)
        Expected   : Exception raised with refund message.
        """
        rest_reject = Restaurant("R03", "Lazy Chef", Restaurant.OPEN)
        rest_reject.simulate_rejection()
        cart = make_cart(("Biryani", 1, 350.0))
        with self.assertRaises(Exception) as ctx:
            self.controller.placeOrder("C013", cart, "UPI", rest_reject)
        self.assertIn("refund", str(ctx.exception).lower())
        print(f"\n[BB-TC-14] PASS | Restaurant rejection + refund | {ctx.exception}")

    # ─────────────────────────────────────────────────────
    # BVA – BOUNDARY VALUE ANALYSIS
    # ─────────────────────────────────────────────────────

    def test_BB_TC_06_cart_total_exactly_1_lower_boundary(self):
        """
        TC ID      : BB-TC-06
        Technique  : BVA – Lower Boundary
        Description: Cart total = ₹1 (exact minimum). Should be accepted.
        Input      : custId=C005, items=[Tea×1 ₹1],
                     payMode=Card, restaurant=OPEN, total=₹1
        Expected   : Order placed successfully. Minimum order accepted.
        """
        cart   = make_cart(("Tea", 1, 1.0))
        result = self.controller.placeOrder("C005", cart, "Card", self.rest_open)
        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 1.0)
        print(f"\n[BB-TC-06] PASS | BVA lower boundary ₹1 accepted | "
              f"OrderID={result['order_id']}")

    def test_BB_TC_07_cart_total_zero_below_minimum(self):
        """
        TC ID      : BB-TC-07
        Technique  : BVA – Below Lower Boundary
        Description: Cart total = ₹0 (below minimum). Must be rejected.
        Input      : custId=C006, items=[FreeItem×1 ₹0],
                     payMode=UPI, restaurant=OPEN, total=₹0
        Expected   : ValidationException – 'Order total must be greater than ₹0.'
        """
        cart = make_cart(("FreeItem", 1, 0.0))
        with self.assertRaises(ValidationException) as ctx:
            self.controller.placeOrder("C006", cart, "UPI", self.rest_open)
        self.assertIn("greater", str(ctx.exception).lower())
        print(f"\n[BB-TC-07] PASS | BVA ₹0 rejected | {ctx.exception}")

    def test_BB_TC_08_cart_total_two_just_above_minimum(self):
        """
        TC ID      : BB-TC-08
        Technique  : BVA – Just Above Minimum
        Description: Cart total = ₹2 (one unit above minimum). Should be accepted.
        Input      : custId=C007, items=[Water×1 ₹2],
                     payMode=Wallet, restaurant=OPEN, total=₹2
        Expected   : Order placed successfully.
        """
        cart   = make_cart(("Water", 1, 2.0))
        result = self.controller.placeOrder("C007", cart, "Wallet", self.rest_open)
        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 2.0)
        print(f"\n[BB-TC-08] PASS | BVA ₹2 accepted (just above min) | "
              f"OrderID={result['order_id']}")

    def test_BB_TC_09_cart_total_10000_upper_boundary(self):
        """
        TC ID      : BB-TC-09
        Technique  : BVA – Upper Boundary
        Description: Cart total = ₹10,000 (exact maximum). Should be accepted.
        Input      : custId=C008, items=[PremiumBox×1 ₹10000],
                     payMode=Card, restaurant=OPEN, total=₹10,000
        Expected   : Order placed successfully. Max cart limit accepted.
        """
        cart   = make_cart(("PremiumBox", 1, 10_000.0))
        result = self.controller.placeOrder("C008", cart, "Card", self.rest_open)
        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 10_000.0)
        print(f"\n[BB-TC-09] PASS | BVA ₹10,000 accepted (upper boundary) | "
              f"OrderID={result['order_id']}")

    def test_BB_TC_10_cart_total_10001_exceeds_max(self):
        """
        TC ID      : BB-TC-10
        Technique  : BVA – Exceeds Upper Boundary
        Description: Cart total = ₹10,001 (one above max). Must be rejected.
        Input      : custId=C009, items=[BulkOrder×1 ₹10001],
                     payMode=UPI, restaurant=OPEN, total=₹10,001
        Expected   : MaxLimitException – 'Cart total exceeds maximum order limit.'
        """
        cart = make_cart(("BulkOrder", 1, 10_001.0))
        with self.assertRaises(MaxLimitException) as ctx:
            self.controller.placeOrder("C009", cart, "UPI", self.rest_open)
        self.assertIn("exceeds", str(ctx.exception).lower())
        print(f"\n[BB-TC-10] PASS | BVA ₹10,001 rejected | {ctx.exception}")

    def test_BB_TC_15_negative_cart_total(self):
        """
        TC ID      : BB-TC-15
        Technique  : BVA – Negative Boundary
        Description: Cart total is negative (qty=-1 injection). Must be blocked.
        Input      : custId=C014, items=[BadItem qty=-1 ₹50],
                     payMode=Card, restaurant=OPEN, total=-₹50
        Expected   : ValueError blocked at CartItem level (quantity must be positive).
        """
        cart = Cart()
        with self.assertRaises(ValueError) as ctx:
            cart.add_item(CartItem("BadItem", -1, 50.0))
        self.assertIn("positive", str(ctx.exception).lower())
        print(f"\n[BB-TC-15] PASS | Negative qty blocked at CartItem | {ctx.exception}")


# ─────────────────────────────────────────────────────────
# CUSTOM TEST RUNNER – prints formatted summary table
# ─────────────────────────────────────────────────────────
class VerboseResult(unittest.TextTestResult):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._outcomes = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self._outcomes.append((test, "PASS"))

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._outcomes.append((test, "FAIL"))

    def addError(self, test, err):
        super().addError(test, err)
        self._outcomes.append((test, "ERROR"))


if __name__ == "__main__":
    print("=" * 70)
    print("  BLACK BOX TEST SUITE – Online Food Ordering System")
    print("  Techniques: ECP (Valid/Invalid) + BVA (Lower/Upper/Negative)")
    print("=" * 70)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None          # keep declaration order
    suite  = loader.loadTestsFromTestCase(BlackBoxTests)

    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)

    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    print("\n" + "=" * 70)
    print(f"  {'TC ID':<12} {'Test Method':<45} {'Result'}")
    print("  " + "-" * 66)

    tc_ids = [
        "BB-TC-01", "BB-TC-11", "BB-TC-12",
        "BB-TC-02", "BB-TC-03", "BB-TC-04", "BB-TC-05",
        "BB-TC-13", "BB-TC-14",
        "BB-TC-06", "BB-TC-07", "BB-TC-08",
        "BB-TC-09", "BB-TC-10", "BB-TC-15",
    ]
    methods = [
        "test_BB_TC_01_valid_order_UPI",
        "test_BB_TC_11_valid_order_Wallet",
        "test_BB_TC_12_valid_order_Card",
        "test_BB_TC_02_null_customer_id",
        "test_BB_TC_03_empty_cart",
        "test_BB_TC_04_invalid_payment_mode",
        "test_BB_TC_05_restaurant_closed",
        "test_BB_TC_13_payment_gateway_failure",
        "test_BB_TC_14_restaurant_rejects_order",
        "test_BB_TC_06_cart_total_exactly_1_lower_boundary",
        "test_BB_TC_07_cart_total_zero_below_minimum",
        "test_BB_TC_08_cart_total_two_just_above_minimum",
        "test_BB_TC_09_cart_total_10000_upper_boundary",
        "test_BB_TC_10_cart_total_10001_exceeds_max",
        "test_BB_TC_15_negative_cart_total",
    ]
    fail_names = {str(f[0]) for f in result.failures + result.errors}
    for tc_id, method in zip(tc_ids, methods):
        status = "FAIL" if method in fail_names else "PASS"
        print(f"  {tc_id:<12} {method:<45} {status}")

    print("  " + "-" * 66)
    print(f"  TOTAL: {total}  |  PASS: {passed}  |  FAIL: {failed}")
    print("=" * 70)
    sys.exit(0 if result.wasSuccessful() else 1)
