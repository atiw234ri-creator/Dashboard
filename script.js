// Sidebar Toggle
const toggleBtn = document.getElementById("toggleBtn");
const sidebar = document.getElementById("sidebar");

toggleBtn.addEventListener("click", () => {
  sidebar.classList.toggle("hide");
});

// Sample Dashboard Data
document.getElementById("users").textContent = "1,250";
document.getElementById("sales").textContent = "850";
document.getElementById("revenue").textContent = "₹1,50,000";
document.getElementById("orders").textContent = "430";