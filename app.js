// document.addEventListener("DOMContentLoaded", () => {
//   const apiUrl = "https://api.example.com/data"; // Replace with your API URL

//   fetch(apiUrl)
//     .then((response) => {
//       if (response.ok) {
//         return response.json();
//       } else {
//         throw new Error("Network response was not ok");
//       }
//     })
//     .then((data) => {
//       const container = document.getElementById("results-container");
//       data.forEach((item) => {
//         const div = document.createElement("div");
//         div.className = "result-item";
//         div.textContent = JSON.stringify(item); // Customize this to display the data as needed
//         container.appendChild(div);
//       });
//     })
//     .catch((error) => {
//       console.error("There was a problem with the fetch operation:", error);
//     });
// });
