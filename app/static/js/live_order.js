/**
 * Live Order Polling (every 5 seconds)
 */
function initLiveOrderPolling(orderId, initialStatus) {
    const statusPill = document.getElementById("order-status-pill");
    const waitTimeVal = document.getElementById("estimated-wait-val");
    const queuePosVal = document.getElementById("queue-pos-val");
    const cancelForm = document.getElementById("cancel-order-form");
    const lastUpdated = document.getElementById("last-polled-time");

    const steps = ["Placed", "Accepted", "Preparing", "Ready", "Collected"];

    function updateStepper(currentStatus) {
        if (currentStatus === "Cancelled") {
            const stepperContainer = document.getElementById("order-stepper");
            if (stepperContainer) {
                stepperContainer.innerHTML = `
                    <div class="alert alert-danger" style="width: 100%; text-align: center; margin: 1rem 0;">
                        <strong>Order Cancelled</strong> - This order has been cancelled and refunded if paid by wallet.
                    </div>
                `;
            }
            return;
        }

        const currentIndex = steps.indexOf(currentStatus);
        steps.forEach((stepName, idx) => {
            const stepElem = document.getElementById(`step-${stepName.toLowerCase()}`);
            if (!stepElem) return;

            stepElem.classList.remove("active", "completed");
            if (idx < currentIndex) {
                stepElem.classList.add("completed");
            } else if (idx === currentIndex) {
                stepElem.classList.add("active");
            }
        });
    }

    // Set initial stepper state
    updateStepper(initialStatus);

    // If already terminal state, don't poll
    if (initialStatus === "Collected" || initialStatus === "Cancelled") {
        return;
    }

    const intervalId = setInterval(async () => {
        try {
            const response = await fetch(`/api/orders/${orderId}/status`);
            if (!response.ok) {
                console.warn("Failed to poll order status:", response.status);
                return;
            }

            const data = await response.json();

            // Update Status Pill
            if (statusPill) {
                statusPill.className = `badge badge-${data.status.toLowerCase()}`;
                statusPill.innerText = data.status;
            }

            // Update queue and wait time
            if (queuePosVal) {
                queuePosVal.innerText = data.queue_position > 0 ? `#${data.queue_position}` : "-";
            }
            if (waitTimeVal) {
                waitTimeVal.innerText = `${data.estimated_wait_minutes} mins`;
            }

            // Update timestamp
            if (lastUpdated) {
                const now = new Date();
                lastUpdated.innerText = now.toLocaleTimeString();
            }

            // Update Stepper
            updateStepper(data.status);

            // Handle cancellation button visibility:
            // Cancellations are only allowed when 'Placed' or 'Accepted'
            if (cancelForm) {
                if (data.status === "Placed" || data.status === "Accepted") {
                    cancelForm.style.display = "block";
                } else {
                    cancelForm.style.display = "none";
                }
            }

            // Stop polling when reaching terminal state
            if (data.status === "Collected" || data.status === "Cancelled") {
                clearInterval(intervalId);
            }
        } catch (err) {
            console.error("Error polling order status:", err);
        }
    }, 5000);
}
