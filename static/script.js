document.addEventListener("DOMContentLoaded", async () => {
  // Auth guard — bounce to login if no active session
  const authCheck = await fetch("/me");
  const authData = await authCheck.json();
  if (!authData.logged_in) {
    window.location.href = "./login.html";
    return;
  }

  const textarea = document.getElementById("note_textarea");
  const titleInput = document.getElementById("note_title");
  const button = document.getElementById("note_submit");
  const output = document.getElementById("myOutput");
  const notesList = document.getElementById("all-notes-list");
  const logoutBtn = document.getElementById("logout_btn");

  if (!textarea || !titleInput || !button || !output) {
    return;
  }

  if (logoutBtn) {
    logoutBtn.addEventListener("click", async () => {
      try {
        await fetch("/logout", { method: "POST" });
      } catch (error) {
        console.error(error);
      } finally {
        window.location.href = "./login.html";
      }
    });
  }

  async function loadTitles() {
    if (!notesList) return;

    try {
      const response = await fetch("/titles");
      const titles = await response.json();

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

  loadTitles();

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
        loadTitles();
      }
    } catch (error) {
      output.textContent = "Failed to save note.";
      console.error(error);
    }
  });
});