/**
 * Cart Manager using LocalStorage for Smart Canteen Ordering System
 */
const Cart = {
    STORAGE_KEY: "smart_canteen_cart",

    getItems() {
        try {
            return JSON.parse(localStorage.getItem(this.STORAGE_KEY)) || [];
        } catch (e) {
            console.error("Failed to parse cart storage", e);
            return [];
        }
    },

    saveItems(items) {
        localStorage.setItem(this.STORAGE_KEY, JSON.stringify(items));
        this.updateBadge();
    },

    addItem(id, name, price, maxStock = 99) {
        const items = this.getItems();
        const existing = items.find(item => item.item_id === id);

        if (existing) {
            if (existing.quantity < maxStock) {
                existing.quantity += 1;
            } else {
                alert(`Cannot add more than ${maxStock} portions of ${name}.`);
                return;
            }
        } else {
            items.push({
                item_id: id,
                name: name,
                price: parseFloat(price),
                quantity: 1,
                maxStock: maxStock
            });
        }

        this.saveItems(items);
        this.showToast(`Added ${name} to cart!`);
    },

    updateQuantity(id, delta) {
        let items = this.getItems();
        const item = items.find(i => i.item_id === id);

        if (item) {
            item.quantity += delta;
            if (item.quantity <= 0) {
                items = items.filter(i => i.item_id !== id);
            } else if (item.maxStock && item.quantity > item.maxStock) {
                item.quantity = item.maxStock;
                alert(`Maximum available stock reached (${item.maxStock}).`);
            }
            this.saveItems(items);
        }
    },

    removeItem(id) {
        let items = this.getItems();
        items = items.filter(i => i.item_id !== id);
        this.saveItems(items);
    },

    clear() {
        localStorage.removeItem(this.STORAGE_KEY);
        this.updateBadge();
    },

    getTotal() {
        return this.getItems().reduce((sum, item) => sum + (item.price * item.quantity), 0);
    },

    getCount() {
        return this.getItems().reduce((count, item) => count + item.quantity, 0);
    },

    updateBadge() {
        const badge = document.getElementById("cart-count-badge");
        if (badge) {
            const count = this.getCount();
            badge.innerText = count;
            badge.style.display = count > 0 ? "inline-block" : "none";
        }
    },

    showToast(message) {
        let toast = document.getElementById("cart-toast");
        if (!toast) {
            toast = document.createElement("div");
            toast.id = "cart-toast";
            toast.style.position = "fixed";
            toast.style.bottom = "20px";
            toast.style.right = "20px";
            toast.style.backgroundColor = "#0f172a";
            toast.style.color = "#ffffff";
            toast.style.padding = "10px 18px";
            toast.style.borderRadius = "8px";
            toast.style.boxShadow = "0 4px 6px rgba(0,0,0,0.15)";
            toast.style.zIndex = "9999";
            toast.style.fontSize = "0.9rem";
            toast.style.transition = "opacity 0.3s ease";
            document.body.appendChild(toast);
        }
        toast.innerText = message;
        toast.style.opacity = "1";
        clearTimeout(this._toastTimeout);
        this._toastTimeout = setTimeout(() => {
            toast.style.opacity = "0";
        }, 2200);
    }
};

document.addEventListener("DOMContentLoaded", () => {
    Cart.updateBadge();

    // Render cart items if on Cart page
    const cartContainer = document.getElementById("cart-items-container");
    if (cartContainer) {
        renderCartPage();
    }

    // Checkout form sync
    const checkoutForm = document.getElementById("checkout-form");
    if (checkoutForm) {
        renderCheckoutSummary();
        checkoutForm.addEventListener("submit", (e) => {
            const items = Cart.getItems();
            if (items.length === 0) {
                e.preventDefault();
                alert("Your cart is empty! Please add items before checking out.");
                return;
            }
            document.getElementById("cart_data_input").value = JSON.stringify(items);
            // Clear cart upon form submit
            setTimeout(() => Cart.clear(), 100);
        });
    }
});

function renderCartPage() {
    const container = document.getElementById("cart-items-container");
    const emptyState = document.getElementById("cart-empty-state");
    const totalElem = document.getElementById("cart-total-amount");
    const checkoutBtn = document.getElementById("proceed-checkout-btn");

    const items = Cart.getItems();

    if (items.length === 0) {
        if (container) container.innerHTML = "";
        if (emptyState) emptyState.style.display = "block";
        if (checkoutBtn) checkoutBtn.style.display = "none";
        if (totalElem) totalElem.innerText = "₹0.00";
        return;
    }

    if (emptyState) emptyState.style.display = "none";
    if (checkoutBtn) checkoutBtn.style.display = "inline-flex";

    let html = "";
    items.forEach(item => {
        const subtotal = (item.price * item.quantity).toFixed(2);
        html += `
            <div class="card" style="margin-bottom: 0.75rem;">
                <div class="card-body" style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.5rem;">
                    <div>
                        <h4 style="margin-bottom: 0.25rem;">${item.name}</h4>
                        <div class="text-muted" style="font-size: 0.9rem;">₹${item.price.toFixed(2)} each</div>
                    </div>
                    <div style="display: flex; align-items: center; gap: 0.75rem;">
                        <div style="display: flex; align-items: center; border: 1px solid var(--border-color); border-radius: 6px; overflow: hidden;">
                            <button type="button" class="btn btn-outline btn-sm" onclick="Cart.updateQuantity(${item.item_id}, -1); renderCartPage();">-</button>
                            <span style="padding: 0 0.75rem; font-weight: 600;">${item.quantity}</span>
                            <button type="button" class="btn btn-outline btn-sm" onclick="Cart.updateQuantity(${item.item_id}, 1); renderCartPage();">+</button>
                        </div>
                        <div style="font-weight: 700; min-width: 70px; text-align: right;">₹${subtotal}</div>
                        <button type="button" class="btn btn-danger btn-sm" onclick="Cart.removeItem(${item.item_id}); renderCartPage();">Remove</button>
                    </div>
                </div>
            </div>
        `;
    });

    container.innerHTML = html;
    if (totalElem) {
        totalElem.innerText = `₹${Cart.getTotal().toFixed(2)}`;
    }
}

function renderCheckoutSummary() {
    const listElem = document.getElementById("checkout-summary-list");
    const totalElem = document.getElementById("checkout-total-val");
    const items = Cart.getItems();

    if (!listElem) return;

    if (items.length === 0) {
        listElem.innerHTML = "<p class='text-muted'>Your cart is empty. <a href='/menu'>Browse Menu</a></p>";
        return;
    }

    let html = "";
    items.forEach(i => {
        html += `
            <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem; font-size: 0.95rem;">
                <span>${i.name} &times; ${i.quantity}</span>
                <span style="font-weight: 600;">₹${(i.price * i.quantity).toFixed(2)}</span>
            </div>
        `;
    });

    listElem.innerHTML = html;
    if (totalElem) {
        totalElem.innerText = `₹${Cart.getTotal().toFixed(2)}`;
    }
}
