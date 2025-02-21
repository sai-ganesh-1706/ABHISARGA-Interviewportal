function toggleSidebar() {
    let sidebar = document.querySelector(".sidebar");
    let content = document.querySelector(".content");

    if (sidebar.style.width === "0px") {
        sidebar.style.width = "250px";
        content.style.marginLeft = "250px";
    } else {
        sidebar.style.width = "0px";
        content.style.marginLeft = "0px";
    }
}

document.addEventListener("DOMContentLoaded", function () {
    console.log("Dashboard Loaded!");

    const toggleSidebar = document.getElementById("toggleSidebar");
    const sidebar = document.querySelector(".sidebar");
    const content = document.querySelector("#content");

    toggleSidebar.addEventListener("click", function () {
        if (sidebar.style.width === "250px" || sidebar.style.width === "") {
            sidebar.style.width = "0px";
            content.style.marginLeft = "0px";
        } else {
            sidebar.style.width = "250px";
            content.style.marginLeft = "250px";
        }
    });
});
