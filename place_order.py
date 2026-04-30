"""
Online Food Ordering System – Place Order Subsystem
Software Engineering Lab Exam | IV B.Tech Computer Engineering
Course: R5IT2009T | VJTI Mumbai
"""

# ─────────────────────────────────────────────
# ENTITY CLASSES (from Q1 Object Model)
# ─────────────────────────────────────────────

class CartItem:
    def __init__(self, name: str, quantity: int, price: float):
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if price < 0:
            raise ValueError("Price cannot be negative.")
        self.name = name
        self.quantity = quantity
        self.price = price

    def subtotal(self) -> float:
        return self.quantity * self.price


class Cart:
    def __init__(self):
        self.items: list[CartItem] = []

    def add_item(self, item: CartItem):
        self.items.append(item)

    def total(self) -> float:
        return sum(item.subtotal() for item in self.items)

    def is_empty(self) -> bool:
        return len(self.items) == 0


class Restaurant:
    OPEN   = "OPEN"
    CLOSED = "CLOSED"

    def __init__(self, restaurant_id: str, name: str, status: str):
        self.restaurant_id = restaurant_id
        self.name          = name
        self.status        = status          # OPEN | CLOSED
        self._will_reject  = False           # simulate rejection scenario

    def is_open(self) -> bool:
        return self.status == Restaurant.OPEN

    def accept_order(self) -> bool:
        """Returns True if restaurant accepts; False to simulate rejection."""
        return not self._will_reject

    def simulate_rejection(self):
        """Test helper – make restaurant reject the next order."""
        self._will_reject = True


class PaymentGateway:
    VALID_MODES = {"UPI", "Card", "Wallet"}

    def __init__(self):
        self._gateway_up = True   # set False to simulate timeout

    def simulate_failure(self):
        self._gateway_up = False

    def process(self, mode: str, amount: float) -> bool:
        if mode not in self.VALID_MODES:
            raise InvalidPaymentException(
                f"Invalid payment method '{mode}'. Choose UPI/Card/Wallet.")
        if not self._gateway_up:
            raise PaymentException("Payment failed. Please retry. Order not placed.")
        return True   # payment successful

    def refund(self, mode: str, amount: float):
        print(f"  [PaymentGateway] Refund of ₹{amount} initiated to {mode}.")


class DeliveryAgent:
    _counter = 1

    def __init__(self):
        self.agent_id   = f"AGT-{DeliveryAgent._counter:03d}"
        self.tracking   = f"TRK-{DeliveryAgent._counter:03d}"
        DeliveryAgent._counter += 1

    @staticmethod
    def assign() -> "DeliveryAgent":
        """Assign nearest available agent (simplified)."""
        return DeliveryAgent()


class Order:
    _counter = 1000

    def __init__(self, customer_id: str, cart: Cart,
                 payment_mode: str, restaurant: Restaurant):
        Order._counter += 1
        self.order_id     = f"ORD-{Order._counter}"
        self.customer_id  = customer_id
        self.cart         = cart
        self.payment_mode = payment_mode
        self.restaurant   = restaurant
        self.status       = "PENDING"
        self.tracking_id  = None

    def __repr__(self):
        return (f"Order({self.order_id}, custId={self.customer_id}, "
                f"total=₹{self.cart.total()}, status={self.status})")


# ─────────────────────────────────────────────
# CUSTOM EXCEPTIONS (Boundary / Control objects)
# ─────────────────────────────────────────────

class ValidationException(Exception):      pass
class EmptyCartException(Exception):        pass
class MaxLimitException(Exception):         pass
class InvalidPaymentException(Exception):   pass
class RestaurantClosedException(Exception): pass
class PaymentException(Exception):          pass


# ─────────────────────────────────────────────
# CONTROL CLASS – OrderController
# ─────────────────────────────────────────────

MAX_ORDER_TOTAL = 10_000.0
MIN_ORDER_TOTAL = 1.0       # ₹0 treated as empty; ₹1 is minimum valid amount


class OrderController:
    """
    placeOrder() control-flow nodes (from whitebox CFG):
    S1 – Validate customerId ≠ null
    S2 – Validate cart not empty
    S3 – Validate cart total > 0 and ≤ 10 000
    S4 – Validate payment mode ∈ {UPI, Card, Wallet}
    S5 – Check restaurant is OPEN
    S6 – processPayment() → if FAIL → raise PaymentException
    S7 – notifyRestaurant() → if REJECT → refund() and raise
    S8 – assignDelivery()
    S9 – Return OrderConfirmation
    Cyclomatic Complexity M = E − N + 2P = 9 decision nodes → M = 10
    """

    def __init__(self, payment_gateway: PaymentGateway):
        self.payment_gateway = payment_gateway

    # ── placeOrder ──────────────────────────────────────────────────────────
    def placeOrder(self, customer_id, cart: Cart,
                   payment_mode: str, restaurant: Restaurant) -> dict:

        # S1 – Validate Customer ID
        if customer_id is None or str(customer_id).strip() == "":
            raise ValidationException("Customer ID cannot be null.")

        # S2 – Validate Cart not empty
        if cart.is_empty():
            raise EmptyCartException(
                "Cart cannot be empty. Add at least one item.")

        # S3 – Validate Cart total bounds
        total = cart.total()
        if total <= 0:
            raise ValidationException("Order total must be greater than ₹0.")
        if total > MAX_ORDER_TOTAL:
            raise MaxLimitException(
                f"Cart total exceeds maximum order limit of ₹{MAX_ORDER_TOTAL:,.0f}.")

        # S4 – Validate Payment mode (gateway also validates, but we check early)
        if payment_mode not in PaymentGateway.VALID_MODES:
            raise InvalidPaymentException(
                f"Invalid payment method. Choose UPI/Card/Wallet.")

        # S5 – Check Restaurant status
        if not restaurant.is_open():
            raise RestaurantClosedException(
                "Restaurant is currently closed. Try later.")

        # S6 – Process Payment
        self.payment_gateway.process(payment_mode, total)  # raises PaymentException on fail

        # S7 – Notify Restaurant / check acceptance
        order = Order(customer_id, cart, payment_mode, restaurant)
        if not restaurant.accept_order():
            self.payment_gateway.refund(payment_mode, total)
            order.status = "REJECTED"
            raise Exception(
                f"Order cancelled by restaurant. Refund of ₹{total} initiated.")

        # S8 – Assign Delivery Agent
        agent = DeliveryAgent.assign()
        order.tracking_id = agent.tracking
        order.status      = "CONFIRMED"

        # S9 – Return Confirmation
        return {
            "order_id"  : order.order_id,
            "status"    : order.status,
            "tracking"  : order.tracking_id,
            "total"     : total,
            "message"   : "Order placed successfully. Confirmation sent.",
        }


# ─────────────────────────────────────────────
# BOUNDARY CLASS – OrderPlacementUI  (simulated)
# ─────────────────────────────────────────────

class OrderPlacementUI:
    """Simulates the boundary (UI) that collects inputs and calls the controller."""

    def __init__(self, controller: OrderController):
        self.controller = controller

    def submit(self, customer_id, cart, payment_mode, restaurant) -> str:
        try:
            result = self.controller.placeOrder(
                customer_id, cart, payment_mode, restaurant)
            return (f"SUCCESS | OrderID: {result['order_id']} | "
                    f"Tracking: {result['tracking']} | Total: ₹{result['total']}")
        except (ValidationException, EmptyCartException,
                MaxLimitException, InvalidPaymentException,
                RestaurantClosedException, PaymentException) as e:
            return f"ERROR | {e}"
        except Exception as e:
            return f"CANCELLED | {e}"


# ─────────────────────────────────────────────
# DEMO / MANUAL TEST RUNNER
# ─────────────────────────────────────────────

def demo():
    gw         = PaymentGateway()
    controller = OrderController(gw)
    ui         = OrderPlacementUI(controller)

    rest_open   = Restaurant("R01", "Spice Garden", Restaurant.OPEN)
    rest_closed = Restaurant("R02", "Night Bites",  Restaurant.CLOSED)

    print("=" * 60)
    print("  Online Food Ordering System – Place Order Demo")
    print("=" * 60)

    # 1. Happy path
    cart1 = Cart()
    cart1.add_item(CartItem("Pizza",  2, 180.0))
    cart1.add_item(CartItem("Burger", 1, 120.0))
    print("\n[TC-01] Valid order (UPI, OPEN, ₹480):")
    print(" ", ui.submit("C001", cart1, "UPI", rest_open))

    # 2. Null customer ID
    cart2 = Cart()
    cart2.add_item(CartItem("Pizza", 1, 180.0))
    print("\n[TC-02] Null Customer ID:")
    print(" ", ui.submit(None, cart2, "Card", rest_open))

    # 3. Empty cart
    cart3 = Cart()
    print("\n[TC-03] Empty cart:")
    print(" ", ui.submit("C002", cart3, "Wallet", rest_open))

    # 4. Invalid payment mode
    cart4 = Cart()
    cart4.add_item(CartItem("Pasta", 1, 250.0))
    print("\n[TC-04] Invalid payment mode (Bitcoin):")
    print(" ", ui.submit("C003", cart4, "Bitcoin", rest_open))

    # 5. Restaurant closed
    cart5 = Cart()
    cart5.add_item(CartItem("Sandwich", 2, 150.0))
    print("\n[TC-05] Restaurant CLOSED:")
    print(" ", ui.submit("C004", cart5, "UPI", rest_closed))

    # 6. BVA – Cart = ₹1 (minimum)
    cart6 = Cart()
    cart6.add_item(CartItem("Tea", 1, 1.0))
    print("\n[TC-06] BVA – Cart total ₹1 (minimum):")
    print(" ", ui.submit("C005", cart6, "Card", rest_open))

    # 7. Cart = ₹0 (below minimum)
    cart7 = Cart()
    cart7.add_item(CartItem("FreeItem", 1, 0.0))
    print("\n[TC-07] BVA – Cart total ₹0:")
    print(" ", ui.submit("C006", cart7, "UPI", rest_open))

    # 8. Cart = ₹10 000 (max boundary)
    cart8 = Cart()
    cart8.add_item(CartItem("PremiumBox", 1, 10_000.0))
    print("\n[TC-08] BVA – Cart total ₹10,000 (max):")
    print(" ", ui.submit("C008", cart8, "Card", rest_open))

    # 9. Cart = ₹10 001 (exceeds max)
    cart9 = Cart()
    cart9.add_item(CartItem("BulkOrder", 1, 10_001.0))
    print("\n[TC-09] BVA – Cart total ₹10,001 (over max):")
    print(" ", ui.submit("C009", cart9, "UPI", rest_open))

    # 10. Payment gateway failure
    gw_fail     = PaymentGateway()
    gw_fail.simulate_failure()
    ctrl_fail   = OrderController(gw_fail)
    ui_fail     = OrderPlacementUI(ctrl_fail)
    cart10 = Cart()
    cart10.add_item(CartItem("Dosa", 2, 80.0))
    print("\n[TC-10] Payment gateway failure:")
    print(" ", ui_fail.submit("C012", cart10, "UPI", rest_open))

    # 11. Restaurant rejects order
    rest_reject = Restaurant("R03", "Lazy Chef", Restaurant.OPEN)
    rest_reject.simulate_rejection()
    cart11 = Cart()
    cart11.add_item(CartItem("Biryani", 1, 350.0))
    print("\n[TC-11] Restaurant rejection / refund:")
    print(" ", ui.submit("C013", cart11, "UPI", rest_reject))

    # 12. Negative cart total guard
    cart12 = Cart()
    try:
        cart12.add_item(CartItem("BadItem", -1, 50.0))
    except ValueError as e:
        print(f"\n[TC-12] Negative quantity blocked at CartItem level: {e}")

    print("\n" + "=" * 60)
    print("  Demo complete.")
    print("=" * 60)


if __name__ == "__main__":
    demo()
