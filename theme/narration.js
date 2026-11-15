// Replaces the audio elements contrib/narration.py puts at the top of a
// chapter with a player that floats at the bottom of the page, opened from
// the menu bar. Without JavaScript the plain audio elements stay.
(function () {
  "use strict";

  const players = document.querySelectorAll(".narration");
  // The print page holds every chapter, each with its own audio, and keeps
  // the plain elements.
  if (players.length !== 1) return;

  const SPEEDS = [1, 1.25, 1.5, 2];
  const PLAY = "M8 5v14l11-7z";
  const PAUSE = "M6 5h4v14H6zM14 5h4v14h-4z";
  const SPEAKER =
    "M3 9v6h4l5 5V4L7 9H3zm13.5 3A4.5 4.5 0 0 0 14 8v8a4.5 4.5 0 0 0 2.5-4zM14 3.2v2.1a7 7 0 0 1 0 13.4v2.1a9 9 0 0 0 0-17.6z";

  // Storage may be refused, in a private window for example; the player
  // then forgets its settings with the page.
  function load(key) {
    try {
      return localStorage.getItem("narration-" + key);
    } catch (e) {
      return null;
    }
  }
  function save(key, value) {
    try {
      localStorage.setItem("narration-" + key, value);
    } catch (e) {}
  }

  function icon(path) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("aria-hidden", "true");
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "path");
    shape.setAttribute("d", path);
    svg.append(shape);
    return svg;
  }

  function element(tag, className, label) {
    const node = document.createElement(tag);
    node.className = className;
    if (tag === "button") node.type = "button";
    if (label) {
      node.title = label;
      node.setAttribute("aria-label", label);
    }
    return node;
  }

  function clock(seconds) {
    if (!isFinite(seconds)) return "--:--";
    const s = Math.floor(seconds);
    return Math.floor(s / 60) + ":" + String(s % 60).padStart(2, "0");
  }

  const audios = Array.from(players[0].querySelectorAll("audio"));
  const sources = new Map(audios.map((a) => [a.title, a.getAttribute("src")]));
  // Each voice's sections, as title and start in seconds.
  const sections = new Map(audios.map((a) => [a.title, JSON.parse(a.dataset.sections || "[]")]));
  const voices = Array.from(sources.keys());
  const savedVoice = load("voice");
  const savedSpeed = Number(load("speed"));
  let voice = voices.includes(savedVoice) ? savedVoice : voices[0];
  let speed = SPEEDS.includes(savedSpeed) ? savedSpeed : 1;
  players[0].hidden = true;

  const audio = new Audio();
  audio.preload = "metadata";
  // The position is kept per audio file, so it resets when the text changes.
  const positionKey = () => "position-" + sources.get(voice);

  const capsule = element("div", "narration-capsule");
  capsule.setAttribute("role", "region");
  capsule.setAttribute("aria-label", "Narration");
  capsule.hidden = true;

  const play = element("button", "narration-play", "Play narration");
  const playIcon = icon(PLAY);
  play.append(playIcon);

  const timeline = element("input", "narration-timeline", "Position");
  timeline.type = "range";
  timeline.min = 0;
  timeline.max = 0;
  timeline.step = "any";
  timeline.value = 0;
  const track = element("div", "narration-track");
  const marks = element("div", "narration-marks");
  track.append(timeline, marks);

  const time = element("span", "narration-time");
  const rate = element("button", "narration-rate", "Playback speed");
  const close = element("button", "narration-close", "Close narration");
  close.textContent = "×";

  capsule.append(play, track, time, rate);
  if (voices.length > 1) {
    const select = element("select", "narration-voice", "Voice");
    for (const v of voices) select.append(new Option(v, v, false, v === voice));
    select.addEventListener("change", () => {
      const at = audio.currentTime;
      const resume = !audio.paused;
      voice = select.value;
      save("voice", voice);
      setSource(at);
      if (resume) audio.play();
    });
    capsule.append(select);
  }
  capsule.append(close);
  document.body.append(capsule);

  const toggle = element("button", "icon-button narration-toggle", "Listen to this page");
  toggle.setAttribute("aria-expanded", "false");
  toggle.append(icon(SPEAKER));
  document.querySelector("#mdbook-menu-bar .left-buttons")?.append(toggle);

  function setSource(at) {
    audio.src = sources.get(voice);
    audio.defaultPlaybackRate = audio.playbackRate = speed;
    audio.addEventListener("loadedmetadata", () => (audio.currentTime = at), { once: true });
  }

  // A mark on the timeline at the start of each of the chapter's main
  // sections, those under its two shallowest heading levels, that jumps to
  // it. A mark closer than 2% to the one before replaces it, so marks never
  // cover each other and a heading right below the title keeps its mark.
  function mark() {
    marks.replaceChildren();
    const headed = sections.get(voice).filter((s) => s.level);
    const deepest = Math.min(...headed.map((s) => s.level)) + 1;
    let last = -Infinity;
    for (const { title, level, start } of sections.get(voice)) {
      const at = (100 * start) / audio.duration;
      if (level > deepest) continue;
      if (at - last < 2) marks.lastChild?.remove();
      last = at;
      const button = element("button", "narration-mark", title || document.title);
      button.style.left = at + "%";
      button.addEventListener("click", () => (audio.currentTime = start));
      marks.append(button);
    }
  }

  function show() {
    const playing = !audio.paused;
    playIcon.firstChild.setAttribute("d", playing ? PAUSE : PLAY);
    play.setAttribute("aria-label", playing ? "Pause narration" : "Play narration");
    play.title = play.getAttribute("aria-label");
    time.textContent = clock(audio.currentTime) + " / " + clock(audio.duration);
    rate.textContent = speed + "×";
    toggle.classList.toggle("narration-active", playing);
  }

  function open(visible) {
    // The audio loads when the player first opens, so a reader who never
    // opens it downloads none of it.
    if (visible && !audio.src) setSource(Number(load(positionKey())) || 0);
    capsule.hidden = !visible;
    toggle.setAttribute("aria-expanded", String(visible));
    if (!visible) audio.pause();
  }

  toggle.addEventListener("click", () => {
    open(capsule.hidden);
    if (!capsule.hidden) play.focus();
  });
  close.addEventListener("click", () => {
    open(false);
    toggle.focus();
  });
  // Only while focus is in the player, so Escape still closes mdbook's search.
  capsule.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    open(false);
    toggle.focus();
  });
  play.addEventListener("click", () => (audio.paused ? audio.play() : audio.pause()));
  rate.addEventListener("click", () => {
    speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length];
    audio.defaultPlaybackRate = audio.playbackRate = speed;
    save("speed", speed);
    show();
  });
  timeline.addEventListener("input", () => (audio.currentTime = Number(timeline.value)));

  audio.addEventListener("loadedmetadata", () => {
    timeline.max = audio.duration;
    mark();
    show();
  });
  audio.addEventListener("timeupdate", () => {
    timeline.value = audio.currentTime;
    timeline.style.setProperty("--progress", (100 * audio.currentTime) / audio.duration + "%");
    save(positionKey(), audio.currentTime);
    show();
  });
  audio.addEventListener("play", show);
  audio.addEventListener("pause", show);
  audio.addEventListener("ended", () => save(positionKey(), 0));

  if ("mediaSession" in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({ title: document.title });
    const skip = (by) => () => (audio.currentTime = Math.max(0, audio.currentTime + by));
    navigator.mediaSession.setActionHandler("play", () => audio.play());
    navigator.mediaSession.setActionHandler("pause", () => audio.pause());
    navigator.mediaSession.setActionHandler("seekbackward", skip(-10));
    navigator.mediaSession.setActionHandler("seekforward", skip(10));
  }

  show();
})();
