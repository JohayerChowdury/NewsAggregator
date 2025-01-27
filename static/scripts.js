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

// Sorting by date
document.getElementById("sortDateAsc").addEventListener("click", () => {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("sort_date", "asc");
  urlParams.delete("sort_title"); // Clear other sorting parameters
  urlParams.delete("page"); // Clear page number
  window.location.search = urlParams.toString();
});

document.getElementById("sortDateDesc").addEventListener("click", () => {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("sort_date", "desc");
  urlParams.delete("sort_title"); // Clear other sorting parameters
  urlParams.delete("page"); // Clear page number
  window.location.search = urlParams.toString();
});

// Sorting by title
document.getElementById("sortTitleAsc").addEventListener("click", () => {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("sort_title", "asc");
  urlParams.delete("sort_date"); // Clear other sorting parameters
  urlParams.delete("page"); // Clear page number
  window.location.search = urlParams.toString();
});

document.getElementById("sortTitleDesc").addEventListener("click", () => {
  const urlParams = new URLSearchParams(window.location.search);
  urlParams.set("sort_title", "desc");
  urlParams.delete("sort_date"); // Clear other sorting parameters
  urlParams.delete("page"); // Clear page number
  window.location.search = urlParams.toString();
});
