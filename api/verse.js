console.log("ALEXANDRA TEST — VERSE SCRIPT IS RUNNING");

console.log("VERSE SCRIPT RUNNING");

async function loadVerse() {
    try {
        const response = await fetch("/api/votd");
        const data = await response.json();

        console.log("VOTD DATA:", data);

        document.getElementById("verse-text").innerText = data.text;
        document.getElementById("verse-ref").innerText = data.reference;

    } catch (error) {
        console.error("VOTD ERROR:", error);
    }
}

loadVerse();
