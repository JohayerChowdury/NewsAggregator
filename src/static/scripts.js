// for sources dialog
const openSourcesDialogButton = document.getElementById("openSourcesDialog");
const closeDialogSourcesButton = document.getElementById("closeSourcesDialog");
const filterSourcesDialog = document.getElementById("filterSourcesDialog");

openSourcesDialogButton.addEventListener("click", () => {
  filterSourcesDialog.showModal();
});

closeDialogSourcesButton.addEventListener("click", () => {
  filterSourcesDialog.close();
});

// for google_searches dialog filter
const openGoogleSearchesDialogButton = document.getElementById("openGoogleSearchDialog");
const closeDialogGoogleSearchesButton = document.getElementById("closeGoogleSearchDialog");
const googleSearchesDialog = document.getElementById("filterGoogleSearchDialog");

openGoogleSearchesDialogButton.addEventListener("click", () => {
  googleSearchesDialog.showModal();
});

closeDialogGoogleSearchesButton.addEventListener("click", () => {
  googleSearchesDialog.close();
});

// for queries description dialog
const openQueriesDialogButton = document.getElementById("openQueriesDescriptionDialog");
const closeDialogQueriesButton = document.getElementById("closeQueriesDescriptionDialog");
const queriesDescriptionDialog = document.getElementById("queriesDescriptionDialog");

openQueriesDialogButton.addEventListener("click", () => {
  queriesDescriptionDialog.showModal();
});

closeDialogQueriesButton.addEventListener("click", () => {
  queriesDescriptionDialog.close();
});

// // hide the loading screen when the page fully loads
// window.addEventListener("load", () => {
//   document.getElementById("loading-screen").style.display = "none";
//   document.getElementById("content").style.display = "block";
// });

// // show loader when the page is loading
// window.addEventListener("beforeunload", () => {
//   document.getElementById("loading-screen").style.display = "block";
//   document.getElementById("content").style.display = "none";
// });
