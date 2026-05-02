const analyticsSource = document.getElementById("analytics-data");
const careerCards = document.querySelectorAll(".career-choice");

careerCards.forEach((card, index) => {
    card.addEventListener("click", () => {
        careerCards.forEach((item) => item.classList.remove("active-card"));
        card.classList.add("active-card");
    });

    if (index === 0) {
        card.classList.add("active-card");
    }
});

if (analyticsSource && window.Chart) {
    const analytics = JSON.parse(analyticsSource.textContent);

    new Chart(document.getElementById("confidenceChart"), {
        type: "bar",
        data: {
            labels: analytics.career_labels,
            datasets: [
                {
                    label: "Confidence Score",
                    data: analytics.confidence_values,
                    backgroundColor: ["#7a6ff0", "#ff7a59", "#0d5d7f", "#8fd694"],
                    borderRadius: 12,
                },
            ],
        },
        options: {
            responsive: true,
            plugins: {
                legend: { display: false },
            },
            scales: {
                y: { beginAtZero: true, max: 100 },
            },
        },
    });

    new Chart(document.getElementById("skillMatchChart"), {
        type: "bar",
        data: {
            labels: analytics.career_labels,
            datasets: [
                {
                    label: "Matched Skills",
                    data: analytics.matched_counts,
                    backgroundColor: "#0d5d7f",
                    borderRadius: 12,
                },
                {
                    label: "Missing Skills",
                    data: analytics.missing_counts,
                    backgroundColor: "#ff7a59",
                    borderRadius: 12,
                },
            ],
        },
        options: {
            responsive: true,
            scales: {
                y: { beginAtZero: true },
            },
        },
    });

    new Chart(document.getElementById("skillGapChart"), {
        type: "pie",
        data: {
            labels: ["Matched Skills", "Missing Skills"],
            datasets: [
                {
                    data: [
                        analytics.matched_counts.reduce((sum, value) => sum + value, 0),
                        analytics.missing_counts.reduce((sum, value) => sum + value, 0),
                    ],
                    backgroundColor: ["#8fd694", "#ff7a59"],
                },
            ],
        },
        options: {
            responsive: true,
        },
    });
}
