document.addEventListener("DOMContentLoaded", () => {
    const textarea = document.getElementById("note_textarea");
    const titleInput = document.getElementById("note_title");
    const button = document.getElementById("note_submit");
    const output = document.getElementById("myOutput");
    const notesList = document.getElementById("all-notes-list");
  
    if (!textarea || !titleInput || !button || !output) {
      return;
    }
  
    async function loadTitles() {
      if (!notesList) return;
  
      try {
        const response = await fetch("/titles");
        const titles = await response.json(); // string array, e.g. ["first note", "second note"]
  
        notesList.innerHTML = "";
  
        if (!titles || titles.length === 0) {
          notesList.textContent = "No notes yet.";
          return;
        }
  
        titles.forEach((title) => {
          const item = document.createElement("div");
          item.textContent = title;
          item.style.cursor = "pointer";
          item.addEventListener("click", () => {
            window.location.href = `./template.html?title=${encodeURIComponent(title)}`;
          });
          notesList.appendChild(item);
        });
      } catch (error) {
        notesList.textContent = "Failed to load notes.";
        console.error(error);
      }
    }
  
    loadTitles(); // populate list on page load
  
    button.addEventListener("click", async () => {
      const note_title = titleInput.value.trim();
      const note_content = textarea.value.trim();
  
      if (!note_title || !note_content) {
        output.textContent = "Please enter both a title and content.";
        return;
      }
  
      try {
        const params = new URLSearchParams({ note_title, note_content });
        const response = await fetch(`/note?${params.toString()}`, {
          method: "POST",
        });
        const data = await response.json();
        output.textContent = data.status;
  
        if (data.status === "Note added successfully") {
          titleInput.value = "";
          textarea.value = "";
          loadTitles(); // refresh the list after adding a note
        }
      } catch (error) {
        output.textContent = "Failed to save note.";
        console.error(error);
      }
    });
  });