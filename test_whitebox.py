"""
=============================================================
 WHITE BOX TESTING – Online Food Ordering System
 Use Case  : Place Order (placeOrder() method)
 Techniques: Statement Coverage & Branch Coverage
             Control Flow Graph (CFG) Analysis
 Course    : Software Engineering (R5IT2009T)
 Institute : VJTI Mumbai | IV B.Tech Computer Engg
=============================================================
 CFG NODES of placeOrder():
   S1 – Validate customerId ≠ null
   S2 – Validate cart not empty
   S3 – Validate cart total > 0 AND ≤ 10,000
   S4 – Validate payment mode ∈ {UPI, Card, Wallet}
   S5 – Check restaurant is OPEN
   S6 – processPayment()   → FAIL → raise PaymentException
   S7 – notifyRestaurant() → REJECT → refund() → raise
   S8 – assignDelivery()
   S9 – return OrderConfirmation

 Cyclomatic Complexity M = 10  (9 decision nodes + 1)

 COVERAGE SUMMARY:
   Statement Coverage : WB-TC-01, 10, 11, 12, 13
   Branch   Coverage  : WB-TC-02 to 09, 14, 15
=============================================================
 HOW TO RUN:
   python test_whitebox.py          <- runs all 15 test cases
   python -m unittest test_whitebox <- same via unittest runner
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
# WHITE BOX TEST CLASS
# ─────────────────────────────────────────────────────────
class WhiteBoxTests(unittest.TestCase):

    def setUp(self):
        """Runs before every test – fresh gateway + controller."""
        self.gw         = PaymentGateway()
        self.controller = OrderController(self.gw)
        self.rest_open  = Restaurant("R01", "Spice Garden", Restaurant.OPEN)
        self.rest_closed= Restaurant("R02", "Night Bites",  Restaurant.CLOSED)

    # ─────────────────────────────────────────────────────
    # STATEMENT COVERAGE
    # ─────────────────────────────────────────────────────

    def test_WB_TC_01_full_happy_path_all_statements(self):
        """
        TC ID         : WB-TC-01
        Coverage Type : Statement Coverage
        Path          : S1(T)→S2(T)→S3(T)→S4(T)→S5(T)→S6(T)→S7(T)→S8→S9
        Description   : Execute the full happy path so every statement in
                        placeOrder() is visited at least once.
        Input         : custId=C001, items=[Pizza×2 ₹360, Burger×1 ₹120],
                        payMode=UPI, restaurant=OPEN, total=₹480
        Statements    : ALL 9 nodes S1–S9 covered
        Branches      : All TRUE branches at every decision node
        Expected      : status=CONFIRMED, OrderID generated, TrackingID returned
        """
        cart   = make_cart(("Pizza", 2, 180.0), ("Burger", 1, 120.0))
        result = self.controller.placeOrder("C001", cart, "UPI", self.rest_open)

        # Verify all key statements executed (S8 → tracking set, S9 → dict returned)
        self.assertEqual(result["status"],  "CONFIRMED")
        self.assertIsNotNone(result["order_id"])
        self.assertIsNotNone(result["tracking"])
        self.assertEqual(result["total"], 480.0)
        self.assertIn("successfully", result["message"])
        print(f"\n[WB-TC-01] PASS | Full path S1–S9 all TRUE | "
              f"OrderID={result['order_id']} Tracking={result['tracking']}")

    def test_WB_TC_10_refund_statement_covered(self):
        """
        TC ID         : WB-TC-10
        Coverage Type : Statement Coverage
        Path          : S6(T)→S7(F)→refund()→notify()→End
        Description   : Cover the refund() statement inside the rejection branch.
                        Without a rejection scenario, refund() is never reached.
        Input         : custId=C009, items=[Dosa×2 ₹250],
                        payMode=UPI, restaurant=OPEN (rejects internally)
        Statements    : refund() and notify() nodes executed
        Expected      : Exception raised with 'refund' in message
        """
        rest_reject = Restaurant("R03", "Lazy Chef", Restaurant.OPEN)
        rest_reject.simulate_rejection()
        cart = make_cart(("Dosa", 2, 125.0))

        with self.assertRaises(Exception) as ctx:
            self.controller.placeOrder("C009", cart, "UPI", rest_reject)
        self.assertIn("refund", str(ctx.exception).lower())
        print(f"\n[WB-TC-10] PASS | refund() statement executed | {ctx.exception}")

    def test_WB_TC_11_delivery_assignment_S8_S9(self):
        """
        TC ID         : WB-TC-11
        Coverage Type : Statement Coverage (S8 focus)
        Path          : S6(T)→S7(T)→S8→S9
        Description   : Verify S8 (assignDelivery) and S9 (ReturnConfirmation)
                        execute when both payment and restaurant acceptance succeed.
        Input         : custId=C010, items=[Thali×2 ₹300],
                        payMode=Card, restaurant=OPEN, total=₹600
        Statements    : S8=assignDelivery, S9=ReturnConfirmation
        Expected      : Delivery agent assigned; TrackingID present in response
        """
        cart   = make_cart(("Thali", 2, 300.0))
        result = self.controller.placeOrder("C010", cart, "Card", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertTrue(result["tracking"].startswith("TRK-"))  # S8 executed
        self.assertIn("order_id", result)                        # S9 executed
        print(f"\n[WB-TC-11] PASS | S8 & S9 executed | "
              f"Tracking={result['tracking']}")

    def test_WB_TC_12_boundary_minimum_S3_true(self):
        """
        TC ID         : WB-TC-12
        Coverage Type : Statement Coverage
        Path          : S3(T at ₹1)→S4(T)→S5(T)→S6(T)→S7(T)→S8→S9
        Description   : Cart total at minimum valid value (₹1) exercises
                        S3-true branch and all subsequent true statements.
        Input         : custId=C011, items=[Tea×1 ₹1],
                        payMode=UPI, restaurant=OPEN, total=₹1
        Statements    : S3-true through S9 all covered
        Expected      : Order placed at minimum valid cart total
        """
        cart   = make_cart(("Tea", 1, 1.0))
        result = self.controller.placeOrder("C011", cart, "UPI", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 1.0)
        print(f"\n[WB-TC-12] PASS | S3-true at ₹1 (min boundary) | "
              f"OrderID={result['order_id']}")

    def test_WB_TC_13_boundary_maximum_S3_true(self):
        """
        TC ID         : WB-TC-13
        Coverage Type : Statement Coverage
        Path          : S3(T at ₹10,000)→S4(T)→S5(T)→S6(T)→S7(T)→S8→S9
        Description   : Cart total at maximum valid value (₹10,000) exercises
                        S3-true branch at the upper limit.
        Input         : custId=C012, items=[PremiumBox×1 ₹10,000],
                        payMode=Card, restaurant=OPEN, total=₹10,000
        Statements    : S3-true at upper boundary through S9
        Expected      : Order placed at maximum valid cart total
        """
        cart   = make_cart(("PremiumBox", 1, 10_000.0))
        result = self.controller.placeOrder("C012", cart, "Card", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 10_000.0)
        print(f"\n[WB-TC-13] PASS | S3-true at ₹10,000 (max boundary) | "
              f"OrderID={result['order_id']}")

    # ─────────────────────────────────────────────────────
    # BRANCH COVERAGE
    # ─────────────────────────────────────────────────────

    def test_WB_TC_02_S1_false_null_customer_id(self):
        """
        TC ID         : WB-TC-02
        Coverage Type : Branch Coverage
        Path          : S1(F) → raise ValidationException
        Description   : Customer ID is null → S1 false branch taken.
                        Covers the null-check false branch at S1.
        Input         : custId=NULL, items=[Pizza×1 ₹180],
                        payMode=Card, restaurant=OPEN
        Branch        : S1 = False  (null check fails)
        Expected      : ValidationException raised
        """
        cart = make_cart(("Pizza", 1, 180.0))
        with self.assertRaises(ValidationException) as ctx:
            self.controller.placeOrder(None, cart, "Card", self.rest_open)
        self.assertIn("null", str(ctx.exception).lower())
        print(f"\n[WB-TC-02] PASS | S1=False branch | {ctx.exception}")

    def test_WB_TC_03_S2_false_empty_cart(self):
        """
        TC ID         : WB-TC-03
        Coverage Type : Branch Coverage
        Path          : S1(T)→S2(F) → raise EmptyCartException
        Description   : Cart is empty → S2 false branch taken.
        Input         : custId=C002, items=[],
                        payMode=Wallet, restaurant=OPEN
        Branch        : S1=True; S2=False
        Expected      : EmptyCartException raised
        """
        cart = Cart()   # empty
        with self.assertRaises(EmptyCartException) as ctx:
            self.controller.placeOrder("C002", cart, "Wallet", self.rest_open)
        self.assertIn("empty", str(ctx.exception).lower())
        print(f"\n[WB-TC-03] PASS | S2=False branch | {ctx.exception}")

    def test_WB_TC_04_S3_false_lower_total_zero(self):
        """
        TC ID         : WB-TC-04
        Coverage Type : Branch Coverage
        Path          : S1(T)→S2(T)→S3(F-lower) → raise ValidationException
        Description   : Cart total = ₹0 → S3 lower false sub-branch taken.
        Input         : custId=C003, items=[FreeItem×1 ₹0],
                        payMode=UPI, restaurant=OPEN, total=₹0
        Branch        : S1=True; S2=True; S3=False (total ≤ 0)
        Expected      : ValidationException – 'Order total must be greater than ₹0.'
        """
        cart = make_cart(("FreeItem", 1, 0.0))
        with self.assertRaises(ValidationException) as ctx:
            self.controller.placeOrder("C003", cart, "UPI", self.rest_open)
        self.assertIn("greater", str(ctx.exception).lower())
        print(f"\n[WB-TC-04] PASS | S3=False(lower) branch | {ctx.exception}")

    def test_WB_TC_05_S3_false_upper_total_exceeds_max(self):
        """
        TC ID         : WB-TC-05
        Coverage Type : Branch Coverage
        Path          : S1(T)→S2(T)→S3(F-upper) → raise MaxLimitException
        Description   : Cart total = ₹15,000 → S3 upper false sub-branch taken.
        Input         : custId=C004, items=[BulkOrder×1 ₹15,000],
                        payMode=Card, restaurant=OPEN, total=₹15,000
        Branch        : S1=True; S2=True; S3=False (total > 10,000)
        Expected      : MaxLimitException – 'Cart total exceeds maximum order limit.'
        """
        cart = make_cart(("BulkOrder", 1, 15_000.0))
        with self.assertRaises(MaxLimitException) as ctx:
            self.controller.placeOrder("C004", cart, "Card", self.rest_open)
        self.assertIn("exceeds", str(ctx.exception).lower())
        print(f"\n[WB-TC-05] PASS | S3=False(upper) branch | {ctx.exception}")

    def test_WB_TC_06_S4_false_invalid_payment_mode(self):
        """
        TC ID         : WB-TC-06
        Coverage Type : Branch Coverage
        Path          : S1(T)→S2(T)→S3(T)→S4(F) → raise InvalidPaymentException
        Description   : Payment mode 'Crypto' is unsupported → S4 false branch taken.
        Input         : custId=C005, items=[Pasta×1 ₹400],
                        payMode=Crypto, restaurant=OPEN, total=₹400
        Branch        : S1–S3=True; S4=False
        Expected      : InvalidPaymentException raised
        """
        cart = make_cart(("Pasta", 1, 400.0))
        with self.assertRaises(InvalidPaymentException) as ctx:
            self.controller.placeOrder("C005", cart, "Crypto", self.rest_open)
        self.assertIn("invalid", str(ctx.exception).lower())
        print(f"\n[WB-TC-06] PASS | S4=False branch | {ctx.exception}")

    def test_WB_TC_07_S5_false_restaurant_closed(self):
        """
        TC ID         : WB-TC-07
        Coverage Type : Branch Coverage
        Path          : S1(T)→S2(T)→S3(T)→S4(T)→S5(F) → raise RestaurantClosedException
        Description   : Restaurant is CLOSED → S5 false branch taken.
        Input         : custId=C006, items=[Rice×1 ₹350],
                        payMode=UPI, restaurant=CLOSED, total=₹350
        Branch        : S1–S4=True; S5=False
        Expected      : RestaurantClosedException raised
        """
        cart = make_cart(("Rice", 1, 350.0))
        with self.assertRaises(RestaurantClosedException) as ctx:
            self.controller.placeOrder("C006", cart, "UPI", self.rest_closed)
        self.assertIn("closed", str(ctx.exception).lower())
        print(f"\n[WB-TC-07] PASS | S5=False branch | {ctx.exception}")

    def test_WB_TC_08_S6_false_payment_gateway_failure(self):
        """
        TC ID         : WB-TC-08
        Coverage Type : Branch Coverage
        Path          : S1–S5(T)→S6(F) → raise PaymentException
        Description   : Gateway is DOWN → S6 false branch (payment fail) taken.
        Input         : custId=C007, items=[Burger×2 ₹140],
                        payMode=Card, gateway=DOWN, restaurant=OPEN, total=₹280
        Branch        : S1–S5=True; S6=False
        Expected      : PaymentException raised; order not created
        """
        self.gw.simulate_failure()
        cart = make_cart(("Burger", 2, 140.0))
        with self.assertRaises(PaymentException) as ctx:
            self.controller.placeOrder("C007", cart, "Card", self.rest_open)
        self.assertIn("failed", str(ctx.exception).lower())
        print(f"\n[WB-TC-08] PASS | S6=False branch | {ctx.exception}")

    def test_WB_TC_09_S7_false_restaurant_rejection(self):
        """
        TC ID         : WB-TC-09
        Coverage Type : Branch Coverage
        Path          : S1–S6(T)→S7(F) → refund()→notify()→End
        Description   : Restaurant rejects the order after payment success.
                        S7 false branch → refund() called.
        Input         : custId=C008, items=[Biryani×1 ₹420],
                        payMode=Wallet, restaurant=OPEN (rejects), total=₹420
        Branch        : S1–S6=True; S7=False
        Expected      : Exception raised; refund initiated
        """
        rest_reject = Restaurant("R04", "Picky Chef", Restaurant.OPEN)
        rest_reject.simulate_rejection()
        cart = make_cart(("Biryani", 1, 420.0))
        with self.assertRaises(Exception) as ctx:
            self.controller.placeOrder("C008", cart, "Wallet", rest_reject)
        self.assertIn("refund", str(ctx.exception).lower())
        print(f"\n[WB-TC-09] PASS | S7=False branch | {ctx.exception}")

    def test_WB_TC_14_S4_true_wallet_payment(self):
        """
        TC ID         : WB-TC-14
        Coverage Type : Branch Coverage
        Path          : S4(T for Wallet)→S5(T)→S6(T)→S7(T)→S8→S9
        Description   : Wallet is the third valid payment mode. Together with
                        TC-01 (UPI) and TC-13 (Card), all S4-true sub-branches
                        are now covered.
        Input         : custId=C013, items=[Rolls×2 ₹150],
                        payMode=Wallet, restaurant=OPEN, total=₹300
        Branch        : S4=True (Wallet); S5–S7=True; S8 & S9 execute
        Expected      : Order placed successfully with Wallet
        """
        cart   = make_cart(("Rolls", 2, 150.0))
        result = self.controller.placeOrder("C013", cart, "Wallet", self.rest_open)

        self.assertEqual(result["status"], "CONFIRMED")
        self.assertEqual(result["total"], 300.0)
        print(f"\n[WB-TC-14] PASS | S4=True(Wallet) branch | "
              f"OrderID={result['order_id']}")

    def test_WB_TC_15_S3_false_negative_total(self):
        """
        TC ID         : WB-TC-15
        Coverage Type : Statement + Branch Coverage
        Path          : S1(T)→S2(T)→S3(F-negative) → raise ValidationException
        Description   : Negative cart total (qty injection) exercises the third
                        sub-branch of S3, completing cyclomatic path coverage.
                        Negative qty is blocked early at CartItem level (ValueError).
                        If it bypasses CartItem, S3 false (total ≤ 0) catches it.
        Input         : custId=C014, items=[BadItem qty=-1 ₹50],
                        payMode=UPI, restaurant=OPEN, total=-₹50
        Branch        : S3=False (negative); 3rd S3 sub-branch exercised
        Expected      : ValueError at CartItem OR ValidationException at S3
        """
        cart = Cart()
        # First test: block at CartItem level (primary defence)
        with self.assertRaises(ValueError) as ctx:
            cart.add_item(CartItem("BadItem", -1, 50.0))
        self.assertIn("positive", str(ctx.exception).lower())
        print(f"\n[WB-TC-15] PASS | Negative boundary S3(F) | {ctx.exception}")

        # Second test: if somehow a zero-total cart slips through, S3 catches it
        cart2 = make_cart(("FreeItem", 1, 0.0))
        with self.assertRaises(ValidationException):
            self.controller.placeOrder("C014", cart2, "UPI", self.rest_open)
        print("         PASS | S3=False(≤0) also verified for zero-total edge case")


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
    print("  WHITE BOX TEST SUITE – Online Food Ordering System")
    print("  Techniques: Statement Coverage + Branch Coverage")
    print("  CFG: S1→S2→S3→S4→S5→S6→S7→S8→S9  |  Cyclomatic Complexity = 10")
    print("=" * 70)

    loader = unittest.TestLoader()
    loader.sortTestMethodsUsing = None
    suite  = loader.loadTestsFromTestCase(WhiteBoxTests)

    runner = unittest.TextTestRunner(verbosity=0, resultclass=VerboseResult)
    result = runner.run(suite)

    total  = result.testsRun
    passed = total - len(result.failures) - len(result.errors)
    failed = len(result.failures) + len(result.errors)

    tc_ids = [
        "WB-TC-01", "WB-TC-10", "WB-TC-11", "WB-TC-12", "WB-TC-13",
        "WB-TC-02", "WB-TC-03", "WB-TC-04", "WB-TC-05",
        "WB-TC-06", "WB-TC-07", "WB-TC-08", "WB-TC-09",
        "WB-TC-14", "WB-TC-15",
    ]
    methods = [
        "test_WB_TC_01_full_happy_path_all_statements",
        "test_WB_TC_10_refund_statement_covered",
        "test_WB_TC_11_delivery_assignment_S8_S9",
        "test_WB_TC_12_boundary_minimum_S3_true",
        "test_WB_TC_13_boundary_maximum_S3_true",
        "test_WB_TC_02_S1_false_null_customer_id",
        "test_WB_TC_03_S2_false_empty_cart",
        "test_WB_TC_04_S3_false_lower_total_zero",
        "test_WB_TC_05_S3_false_upper_total_exceeds_max",
        "test_WB_TC_06_S4_false_invalid_payment_mode",
        "test_WB_TC_07_S5_false_restaurant_closed",
        "test_WB_TC_08_S6_false_payment_gateway_failure",
        "test_WB_TC_09_S7_false_restaurant_rejection",
        "test_WB_TC_14_S4_true_wallet_payment",
        "test_WB_TC_15_S3_false_negative_total",
    ]
    coverage_type = [
        "Statement", "Statement", "Statement", "Statement", "Statement",
        "Branch", "Branch", "Branch", "Branch",
        "Branch", "Branch", "Branch", "Branch",
        "Branch", "Stmt+Branch",
    ]
    path = [
        "S1–S9 ALL TRUE",
        "S7(F)→refund()",
        "S6–S7(T)→S8→S9",
        "S3(T,₹1)→S4–S9",
        "S3(T,₹10k)→S4–S9",
        "S1(F)→Exception",
        "S1(T)→S2(F)→Exc",
        "S3(F-lower)→Exc",
        "S3(F-upper)→Exc",
        "S4(F)→Exception",
        "S5(F)→Exception",
        "S6(F)→Exception",
        "S7(F)→refund()",
        "S4(T,Wallet)→S8–S9",
        "S3(F-negative)→Exc",
    ]

    fail_names = {str(f[0]) for f in result.failures + result.errors}

    print("\n" + "=" * 90)
    print(f"  {'TC ID':<10} {'Coverage':<14} {'Path':<22} {'Method':<38} {'Result'}")
    print("  " + "-" * 86)
    for tc_id, method, cov, pth in zip(tc_ids, methods, coverage_type, path):
        status = "FAIL" if method in fail_names else "PASS"
        print(f"  {tc_id:<10} {cov:<14} {pth:<22} {method:<38} {status}")
    print("  " + "-" * 86)
    print(f"  TOTAL: {total}  |  PASS: {passed}  |  FAIL: {failed}")
    print("=" * 90)
    sys.exit(0 if result.wasSuccessful() else 1)
