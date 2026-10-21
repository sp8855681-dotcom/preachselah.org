const defaultTopics = JSON.parse(document.getElementById("topic-data").textContent);
const topicList = document.getElementById("topic-list");
let customTopics = [];
try {
  const savedTopics = JSON.parse(localStorage.getItem("preachselah-custom-topics") || "[]");
  if (Array.isArray(savedTopics)) {
    customTopics = savedTopics.filter((topic) =>
      topic && typeof topic.title === "string" && typeof topic.category === "string" &&
      typeof topic.reference === "string" &&
      typeof topic.verse === "string" && typeof topic.hint === "string" &&
      Array.isArray(topic.points) && topic.points.every((point) => typeof point === "string")
    );
  }
} catch {}
let topics = [...defaultTopics, ...customTopics];
let currentTopic = 0;

function saveCustomTopics() {
  try {
    localStorage.setItem("preachselah-custom-topics", JSON.stringify(customTopics));
    return true;
  } catch {
    return false;
  }
}

function clearSavedTopics() {
  try {
    localStorage.removeItem("preachselah-custom-topics");
    return true;
  } catch {
    return false;
  }
}

function renderTopicButtons() {
  topicList.replaceChildren(...topics.map((topic, index) => {
    const button = document.createElement("button");
    button.className = `topic-chip${index === currentTopic ? " active" : ""}`;
    button.type = "button";
    button.dataset.topic = String(index);
    const dot = document.createElement("span");
    dot.className = "topic-chip-dot";
    button.append(dot, document.createTextNode(topic.title));
    button.addEventListener("click", () => showTopic(index));
    return button;
  }));
}

function showTopic(index) {
  if (index < 0 || index >= topics.length) return;
  currentTopic = index;
  const topic = topics[index];
  document.getElementById("topic-category").textContent = topic.category;
  document.getElementById("topic-title").textContent = topic.title;
  document.getElementById("topic-reference").replaceChildren(
    document.createTextNode(`${topic.reference} `),
    Object.assign(document.createElement("span"), { textContent: "↗" })
  );
  document.getElementById("topic-verse").textContent = `“${topic.verse}”`;
  document.getElementById("topic-hint").textContent = topic.hint;
  const points = document.getElementById("topic-points");
  points.replaceChildren(...topic.points.map((point) => {
    const item = document.createElement("li");
    item.textContent = point;
    return item;
  }));
  topicList.querySelectorAll(".topic-chip").forEach((button, buttonIndex) =>
    button.classList.toggle("active", buttonIndex === index)
  );
}

renderTopicButtons();
showTopic(0);
document.getElementById("surprise-button").addEventListener("click", () => {
  if (topics.length > 1) {
    const next = Math.floor(Math.random() * (topics.length - 1));
    showTopic(next >= currentTopic ? next + 1 : next);
  }
});
document.getElementById("reset-topics").addEventListener("click", () => {
  customTopics = [];
  topics = [...defaultTopics];
  currentTopic = 0;
  const cleared = clearSavedTopics();
  renderTopicButtons();
  showTopic(0);
  document.getElementById("topic-form-message").textContent = cleared
    ? "Your original topic suggestions are back."
    : "Your original suggestions are back for now, but browser storage could not be cleared.";
});
document.getElementById("custom-topic-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const input = document.getElementById("custom-topic-input");
  const message = document.getElementById("topic-form-message");
  const submitButton = document.getElementById("create-topic-button");
  const title = input.value.trim();
  if (!title) {
    message.textContent = "Enter a topic to get started.";
    return;
  }
  submitButton.disabled = true;
  message.textContent = "Finding a Scripture starting point…";
  try {
    const response = await fetch("/api/topic", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title })
    });
    const topic = await response.json();
    if (!response.ok) throw new Error(topic.error || "Your topic could not be created.");
    const existingIndex = topics.findIndex((item) => item.title.toLocaleLowerCase() === topic.title.toLocaleLowerCase());
    if (existingIndex !== -1) {
      showTopic(existingIndex);
    } else {
      customTopics.push(topic);
      topics.push(topic);
      currentTopic = topics.length - 1;
      renderTopicButtons();
      showTopic(currentTopic);
    }
    input.value = "";
    const saved = saveCustomTopics();
    message.textContent = saved
      ? `“${topic.title}” is ready. Your custom topics stay saved in this browser until reset.`
      : `“${topic.title}” is ready, but browser storage is unavailable so it will not stay after you leave.`;
  } catch (error) {
    message.textContent = error.message;
  } finally {
    submitButton.disabled = false;
  }
});
document.getElementById("copy-topic").addEventListener("click", async (event) => {
  const topic = topics[currentTopic];
  const notes = `${topic.title} — ${topic.reference}\n\n${topic.verse}\n\n${topic.hint}\n\n${topic.points.map((point, index) => `${index + 1}. ${point}`).join("\n")}`;
  const button = event.currentTarget;
  try {
    await navigator.clipboard.writeText(notes);
    button.innerHTML = "Copied <span>✓</span>";
    window.setTimeout(() => { button.innerHTML = 'Copy notes <span>⧉</span>'; }, 1800);
  } catch {
    button.textContent = "Copy unavailable";
    window.setTimeout(() => { button.innerHTML = 'Copy notes <span>⧉</span>'; }, 1800);
  }
});

const bookSelect = document.getElementById("book-select");
const chapterSelect = document.getElementById("chapter-select");
const placeholder = document.getElementById("reader-placeholder");
const loading = document.getElementById("reader-loading");
const errorBox = document.getElementById("reader-error");
const chapterText = document.getElementById("chapter-text");

function updateChapters() {
  const total = Number(bookSelect.selectedOptions[0].dataset.chapters);
  chapterSelect.replaceChildren(...Array.from({ length: total }, (_, index) => {
    const option = document.createElement("option");
    option.value = String(index + 1);
    option.textContent = `Chapter ${index + 1}`;
    return option;
  }));
}

async function loadChapter() {
  const book = bookSelect.value;
  const chapter = chapterSelect.value;
  placeholder.hidden = true;
  chapterText.hidden = true;
  errorBox.hidden = true;
  loading.hidden = false;
  document.getElementById("load-chapter").disabled = true;
  try {
    const response = await fetch(`/api/chapter?book=${encodeURIComponent(book)}&chapter=${encodeURIComponent(chapter)}`);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || "The chapter could not be loaded.");
    document.getElementById("chapter-title").textContent = data.reference;
    const verses = document.getElementById("chapter-verses");
    verses.replaceChildren(...data.verses.map((verse) => {
      const paragraph = document.createElement("p");
      paragraph.className = "bible-verse";
      const number = document.createElement("sup");
      number.textContent = verse.number;
      paragraph.append(number, document.createTextNode(` ${verse.text}`));
      return paragraph;
    }));
    chapterText.hidden = false;
  } catch (error) {
    errorBox.textContent = error.message;
    errorBox.hidden = false;
  } finally {
    loading.hidden = true;
    document.getElementById("load-chapter").disabled = false;
  }
}

bookSelect.addEventListener("change", updateChapters);
document.getElementById("load-chapter").addEventListener("click", loadChapter);
document.getElementById("read-first-chapter").addEventListener("click", () => {
  bookSelect.value = "Genesis";
  updateChapters();
  chapterSelect.value = "1";
  loadChapter();
  document.getElementById("bible").scrollIntoView({ behavior: "smooth" });
});
document.getElementById("topic-reference").addEventListener("click", () => {
  const [book, chapter] = topics[currentTopic].reference.match(/^(.*)\s+(\d+)/).slice(1);
  bookSelect.value = book;
  updateChapters();
  chapterSelect.value = chapter;
  loadChapter();
});
updateChapters();

const welcomeModal = document.getElementById("welcome-modal");
if (welcomeModal) {
  const closeWelcome = () => {
    welcomeModal.remove();
    document.getElementById("topics").scrollIntoView({ behavior: "smooth" });
  };
  document.getElementById("welcome-close").addEventListener("click", closeWelcome);
  document.getElementById("welcome-begin").addEventListener("click", closeWelcome);
  welcomeModal.addEventListener("click", (event) => {
    if (event.target === welcomeModal) closeWelcome();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && welcomeModal.isConnected) closeWelcome();
  });
  document.getElementById("welcome-begin").focus();
}
