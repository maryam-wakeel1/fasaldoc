const form = document.querySelector("#diagnosisForm");
const cameraInput = document.querySelector("#cameraInput");
const micButton = document.querySelector("#micButton");
const micLabel = document.querySelector("#micLabel");
const micHint = document.querySelector("#micHint");
const recordingStatus = document.querySelector("#recordingStatus");
const imagePreview = document.querySelector("#imagePreview");
const imageEmpty = document.querySelector("#imageEmpty");
const imageName = document.querySelector("#imageName");
const questionInput = document.querySelector("#textQuestion");
const analyzeButton = document.querySelector("#analyzeButton");
const statusMessage = document.querySelector("#statusMessage");
const resultsCard = document.querySelector("#resultsCard");
const demoBanner = document.querySelector("#demoBanner");
const diagnosisText = document.querySelector("#diagnosisText");
const symptomsText = document.querySelector("#symptomsText");
const treatmentText = document.querySelector("#treatmentText");
const confidenceText = document.querySelector("#confidenceText");
const confidenceFill = document.querySelector("#confidenceFill");
const uncertaintyWarning = document.querySelector("#uncertaintyWarning");
const referenceGallery = document.querySelector("#referenceGallery");
const referenceStrip = document.querySelector("#referenceStrip");
const resultAudio = document.querySelector("#resultAudio");
const playAudioButton = document.querySelector("#playAudioButton");
const audioNote = document.querySelector("#audioNote");
const newDiagnosisButton = document.querySelector("#newDiagnosisButton");
const langToggle = document.querySelector("#langToggle");

let selectedImage = null;
let imageObjectUrl = null;
let recordedAudio = null;
let mediaRecorder = null;
let mediaStream = null;
let audioChunks = [];
let currentLang = "ur";
let isAnalyzing = false;

const translations = {
  ur: {
    title: "FasalDoc | فصل ڈاکٹر",
    brandAria: "فصل ڈاکٹر",
    eyebrow: "آپ کی فصل، آپ کی زبان",
    brandSubtitle: "(فصل ڈاکٹر)",
    tagline: "اپنی فصل کی آواز میں بات کریں",
    langToggle: "EN / اردو",
    introTitle: "پتے کی تصویر لیں",
    introHint: "صاف روشنی میں متاثرہ پتا قریب سے دکھائیں۔",
    captureAria: "تصویر اور آواز",
    cameraLabel: "تصویر لیں",
    cameraHint: "کیمرہ کھولیں",
    micLabel: "آواز ریکارڈ کریں",
    micHint: "اپنا سوال بولیں",
    recordingStatus: "آواز ریکارڈ ہو رہی ہے — مکمل ہونے پر مائیک دبائیں",
    previewAria: "منتخب تصویر",
    previewEmpty: "ابھی تصویر منتخب نہیں ہوئی",
    previewAlt: "منتخب فصل کے پتے کی تصویر",
    questionLabel: "لکھ کر بھی پوچھ سکتے ہیں (اختیاری)",
    questionPlaceholder: "مثلاً: پتے پیلے کیوں ہیں؟",
    analyzeButton: "تشخیص کریں",
    demoBanner: "یہ صرف نمونہ ہے — اصل تشخیص نہیں",
    resultHeading: "ممکنہ مسئلہ",
    confidenceLabel: "یقین کی سطح",
    confidenceTrack: "یقین کی سطح",
    symptomsHeading: "پتے پر کیا نظر آیا",
    treatmentHeading: "سادہ رہنمائی",
    referenceTitle: "ملتی جلتی حوالہ جاتی تصویریں",
    referenceHint: "یہ مثالیں ہیں؛ اپنے کھیت کی حالت کے لیے مقامی ماہر سے تصدیق کریں۔",
    warningTitle: "قریبی زرعی ماہر سے تصدیق کریں",
    warningText: "تصویر سے پوری طرح یقین نہیں ہو سکا۔",
    audioSection: "جواب سنیں",
    playAudio: "جواب سنیں",
    newDiagnosis: "نئی تصویر لیں",

    micStop: "ریکارڈنگ روکیں",
    micReady: "آواز تیار ہے",
    micPressFinish: "دباکر مکمل کریں",
    manualPlayNote: "جواب سننے کے لیے بٹن دبائیں۔",
    captionFallback: "فصل کی حوالہ جاتی تصویر",
    altTemplate: "حوالہ جاتی تصویر: ",
    needsVerification: "اس مثال کی تصدیق درکار ہے",
    audioPlaying: "جواب چل رہا ہے۔",
    errImageTypeSize: "براہ کرم 10 MB سے چھوٹی JPG، PNG یا WEBP تصویر منتخب کریں۔",
    imageReady: "تصویر تیار ہے۔ چاہیں تو اپنا سوال بولیں، پھر تشخیص کریں۔",
    errNoMic: "اس آلے میں آواز ریکارڈ نہیں ہو سکتی۔ آپ سوال لکھ سکتے ہیں۔",
    audioReady: "آواز تیار ہے۔ اب تشخیص کریں۔",
    audioLost: "آواز محفوظ نہیں ہوئی، تصویر سے رہنمائی جاری رکھی جا سکتی ہے۔",
    errMicDenied: "مائیک کی اجازت نہیں ملی۔ آپ سوال لکھ سکتے ہیں۔",
    errNeedImage: "پہلے فصل کے پتے کی تصویر لیں۔",
    errNeedRecording: "پہلے آواز کی ریکارڈنگ مکمل کریں۔",
    analyzing: "تشخیص ہو رہی ہے",
    analyzingStatus: "تصویر دیکھی جا رہی ہے، براہ کرم انتظار کریں",
    errFallback: "تشخیص مکمل نہیں ہو سکی۔ دوبارہ کوشش کریں۔",
    doneStatus: "تشخیص مکمل ہو گئی۔",
    errNetwork: "انٹرنیٹ یا سرور سے رابطہ نہیں ہو سکا۔",
    noSymptoms: "تصویر سے واضح علامات نہیں مل سکیں۔",
    confidenceTemplate: "% یقین",
    audioUnavailable: "آواز دستیاب نہیں، اوپر دیا گیا جواب پڑھیں۔",
    newStatus: "نئی تصویر لے کر شروع کریں۔",
  },
  en: {
    title: "FasalDoc | Crop Doctor",
    brandAria: "Crop Doctor",
    eyebrow: "Your crop, your language",
    brandSubtitle: "(Crop Doctor)",
    tagline: "Talk to your crop in your own voice",
    langToggle: "اردو / EN",
    introTitle: "Take a leaf photo",
    introHint: "Show the affected leaf up close in clear light.",
    captureAria: "Image and voice",
    cameraLabel: "Take photo",
    cameraHint: "Open camera",
    micLabel: "Record voice",
    micHint: "Ask your question",
    recordingStatus: "Recording voice — press mic again when done",
    previewAria: "Selected image",
    previewEmpty: "No image selected yet",
    previewAlt: "Selected crop leaf image",
    questionLabel: "You can also type a question (optional)",
    questionPlaceholder: "For example: why are the leaves yellow?",
    analyzeButton: "Diagnose",
    demoBanner: "This is only a demo — not a real diagnosis",
    resultHeading: "Likely issue",
    confidenceLabel: "Confidence level",
    confidenceTrack: "Confidence level",
    symptomsHeading: "What the leaf shows",
    treatmentHeading: "Simple guidance",
    referenceTitle: "Matching reference images",
    referenceHint: "These are examples; please confirm with a local expert for your field.",
    warningTitle: "Confirm with a local agriculture expert",
    warningText: "The image alone did not give full certainty.",
    audioSection: "Listen to the answer",
    playAudio: "Listen to the answer",
    newDiagnosis: "Take a new photo",

    micStop: "Stop recording",
    micReady: "Voice ready",
    micPressFinish: "Press to finish",
    manualPlayNote: "Press the button to listen to the answer.",
    captionFallback: "Crop reference image",
    altTemplate: "Reference image: ",
    needsVerification: "This example needs verification",
    audioPlaying: "Answer is playing.",
    errImageTypeSize: "Please choose a JPG, PNG, or WEBP image smaller than 10 MB.",
    imageReady: "Image is ready. You can record your question, then diagnose.",
    errNoMic: "This device cannot record voice. You can type a question instead.",
    audioReady: "Voice is ready. Now run the diagnosis.",
    audioLost: "Voice was not saved; continuing with the image is fine.",
    errMicDenied: "Microphone permission was denied. You can type a question.",
    errNeedImage: "Please take a crop leaf photo first.",
    errNeedRecording: "Please finish the voice recording first.",
    analyzing: "Diagnosing",
    analyzingStatus: "Analyzing the image, please wait",
    errFallback: "Diagnosis could not be completed. Please try again.",
    doneStatus: "Diagnosis complete.",
    errNetwork: "Could not reach the internet or server.",
    noSymptoms: "No clear signs could be read from the image.",
    confidenceTemplate: "% confidence",
    audioUnavailable: "Audio is not available. Please read the answer above.",
    newStatus: "Start with a new photo.",
  },
};

function t(key) {
  return translations[currentLang]?.[key] ?? translations.ur[key] ?? "";
}

function applyLanguage(lang) {
  currentLang = lang === "en" ? "en" : "ur";
  const dict = translations[currentLang];

  document.documentElement.lang = currentLang;
  document.documentElement.dir = currentLang === "en" ? "ltr" : "rtl";
  document.body.classList.toggle("lang-en", currentLang === "en");
  document.body.classList.toggle("lang-ur", currentLang === "ur");

  document.querySelectorAll("[data-i18n]").forEach((element) => {
    const key = element.getAttribute("data-i18n");
    if (dict[key] !== undefined) {
      element.textContent = dict[key];
    }
  });
  document.querySelectorAll("[data-i18n-attr]").forEach((element) => {
    const raw = element.getAttribute("data-i18n-attr") || "";
    raw.split(/\s+/).filter(Boolean).forEach((entry) => {
      const [attr, key] = entry.split(":");
      if (attr && key && dict[key] !== undefined) {
        element.setAttribute(attr, dict[key]);
      }
    });
  });

  if (langToggle) langToggle.setAttribute("aria-pressed", currentLang === "en" ? "true" : "false");

  if (!isAnalyzing && statusMessage && statusMessage.dataset.statusKey) {
    setStatus(t(statusMessage.dataset.statusKey), statusMessage.dataset.statusType || "");
  }
  if (mediaRecorder?.state === "recording" || recordedAudio) {
    refreshRecordingLabels();
  }
}

function refreshRecordingLabels() {
  const isRecording = mediaRecorder?.state === "recording";
  if (!micLabel || !micHint) return;
  micLabel.textContent = isRecording ? t("micStop") : t("micLabel");
  micHint.textContent = isRecording
    ? t("micPressFinish")
    : recordedAudio
    ? t("micReady")
    : t("micHint");
}

function initLanguage() {
  let stored = "ur";
  try {
    const raw = window.localStorage.getItem("fasaldoc.language");
    if (raw === "en" || raw === "ur") stored = raw;
  } catch {
    stored = "ur";
  }
  applyLanguage(stored);
}

if (langToggle) {
  langToggle.addEventListener("click", () => {
    const next = currentLang === "en" ? "ur" : "en";
    try {
      window.localStorage.setItem("fasaldoc.language", next);
    } catch {
      /* storage may be disabled; continue */
    }
    applyLanguage(next);
  });
}

function setStatus(message = "", type = "", statusKey = "") {
  statusMessage.textContent = message;
  statusMessage.className = `status-message ${type}`.trim();
  statusMessage.dataset.statusKey = statusKey || "";
  statusMessage.dataset.statusType = type || "";
}

function setRecording(isRecording) {
  micButton.classList.toggle("is-recording", isRecording);
  micButton.setAttribute("aria-pressed", String(isRecording));
  refreshRecordingLabels();
  recordingStatus.hidden = !isRecording;
}

function supportedAudioOptions() {
  const mimeTypes = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg;codecs=opus"];
  const mimeType = mimeTypes.find((type) => MediaRecorder.isTypeSupported(type));
  return mimeType ? { mimeType } : undefined;
}

function showManualPlay(note = t("manualPlayNote")) {
  playAudioButton.hidden = false;
  audioNote.textContent = note;
}

function clearReferenceImages() {
  referenceStrip.replaceChildren();
  referenceGallery.hidden = true;
}

function staticReferenceImageUrl(value) {
  if (typeof value !== "string") return null;
  try {
    const url = new URL(value, window.location.origin);
    if (url.origin !== window.location.origin || !url.pathname.startsWith("/static/assets/images/")) {
      return null;
    }
    return url.href;
  } catch {
    return null;
  }
}

function renderReferenceImages(references) {
  clearReferenceImages();
  if (!Array.isArray(references)) return;

  for (const reference of references) {
    const imageUrl = staticReferenceImageUrl(reference?.url);
    if (!imageUrl) continue;

    const figure = document.createElement("figure");
    figure.className = "reference-item";

    const image = document.createElement("img");
    const captionText =
      (currentLang === "en"
        ? reference.caption_english || reference.caption_urdu || reference.disease
        : reference.caption_urdu || reference.caption_english || reference.disease) || t("captionFallback");
    image.alt = `${t("altTemplate")}${captionText}`;
    image.loading = "lazy";
    image.decoding = "async";
    image.addEventListener("error", () => {
      figure.remove();
      referenceGallery.hidden = referenceStrip.childElementCount === 0;
    });
    image.src = imageUrl;

    const caption = document.createElement("figcaption");
    caption.textContent = captionText;
    figure.append(image, caption);

    if (reference.needs_verification === true) {
      const notice = document.createElement("span");
      notice.className = "reference-needs-verification";
      notice.textContent = t("needsVerification");
      figure.append(notice);
    }

    referenceStrip.append(figure);
  }

  referenceGallery.hidden = referenceStrip.childElementCount === 0;
}

async function playResponseAudio() {
  if (!resultAudio.src) {
    return;
  }
  try {
    await resultAudio.play();
    playAudioButton.hidden = true;
    audioNote.textContent = t("audioPlaying");
  } catch {
    showManualPlay();
  }
}

cameraInput.addEventListener("change", () => {
  const [file] = cameraInput.files;
  if (!file) return;

  const validTypes = ["image/jpeg", "image/png", "image/webp"];
  if (!validTypes.includes(file.type) || file.size > 10 * 1024 * 1024) {
    selectedImage = null;
    analyzeButton.disabled = true;
    setStatus(t("errImageTypeSize"), "error", "errImageTypeSize");
    return;
  }

  if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
  selectedImage = file;
  imageObjectUrl = URL.createObjectURL(file);
  imagePreview.src = imageObjectUrl;
  imagePreview.hidden = false;
  imageEmpty.hidden = true;
  imageName.textContent = file.name;
  imageName.hidden = false;
  analyzeButton.disabled = false;
  resultsCard.hidden = true;
  setStatus(t("imageReady"), "", "imageReady");
});

micButton.addEventListener("click", async () => {
  if (mediaRecorder?.state === "recording") {
    mediaRecorder.stop();
    return;
  }

  if (!navigator.mediaDevices?.getUserMedia || !window.MediaRecorder) {
    setStatus(t("errNoMic"), "error", "errNoMic");
    return;
  }

  try {
    mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(mediaStream, supportedAudioOptions());
    audioChunks = [];
    mediaRecorder.addEventListener("dataavailable", (event) => {
      if (event.data.size) audioChunks.push(event.data);
    });
    mediaRecorder.addEventListener("stop", () => {
      const mimeType = mediaRecorder.mimeType || "audio/webm";
      recordedAudio = new Blob(audioChunks, { type: mimeType });
      mediaStream?.getTracks().forEach((track) => track.stop());
      mediaStream = null;
      setRecording(false);
      if (recordedAudio.size) {
        setStatus(t("audioReady"), "", "audioReady");
      } else {
        setStatus(t("audioLost"), "", "audioLost");
      }
    });
    mediaRecorder.start();
    setRecording(true);
    setStatus("");
  } catch {
    setStatus(t("errMicDenied"), "error", "errMicDenied");
  }
});

function setAnalyzeIdleState() {
  isAnalyzing = false;
  analyzeButton.disabled = false;
  analyzeButton.replaceChildren();
  const iconWrapper = document.createElement("span");
  iconWrapper.setAttribute("aria-hidden", "true");
  const icon = document.createElement("i");
  icon.className = "fa-solid fa-magnifying-glass";
  iconWrapper.append(icon);
  const label = document.createElement("span");
  label.setAttribute("data-i18n", "analyzeButton");
  label.textContent = t("analyzeButton");
  analyzeButton.append(iconWrapper, label);
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!selectedImage) {
    setStatus(t("errNeedImage"), "error", "errNeedImage");
    return;
  }
  if (mediaRecorder?.state === "recording") {
    setStatus(t("errNeedRecording"), "error", "errNeedRecording");
    return;
  }

  isAnalyzing = true;
  analyzeButton.disabled = true;
  const workingLabel = document.createElement("span");
  workingLabel.textContent = t("analyzing");
  analyzeButton.replaceChildren(workingLabel);
  setStatus(t("analyzingStatus"), "loading", "analyzingStatus");
  resultsCard.hidden = true;

  const data = new FormData();
  data.append("image", selectedImage);
  if (recordedAudio?.size) data.append("audio", recordedAudio, "voice-question.webm");
  if (questionInput.value.trim()) data.append("text_question", questionInput.value.trim());
  data.append("language", currentLang);

  try {
    const response = await fetch("/api/diagnose", { method: "POST", body: data });
    const payload = await response.json();
    if (!response.ok) {
      const detail = payload.detail || {};
      const message =
        (currentLang === "en" ? detail.message_english : detail.message_urdu) ||
        detail.message_urdu ||
        detail.message_english ||
        t("errFallback");
      throw new Error(message);
    }
    renderResults(payload);
    setStatus(t("doneStatus"), "", "doneStatus");
  } catch (error) {
    setStatus(error.message || t("errNetwork"), "error");
  } finally {
    setAnalyzeIdleState();
  }
});

function renderResults(payload) {
  const lang = payload.language === "en" ? "en" : currentLang;
  diagnosisText.textContent =
    (lang === "en" ? payload.diagnosis_english : payload.diagnosis_urdu) || payload.diagnosis_urdu || "";
  const symptoms =
    (lang === "en" ? payload.visual_symptoms_english : payload.visual_symptoms_urdu) ||
    payload.visual_symptoms_urdu;
  symptomsText.textContent = symptoms || t("noSymptoms");
  treatmentText.textContent =
    (lang === "en" ? payload.treatment_plan_english : payload.treatment_plan_urdu) ||
    payload.treatment_plan_urdu || "";
  const confidence = Math.max(0, Math.min(100, Number(payload.confidence_score) || 0));
  confidenceText.textContent = `${confidence}${t("confidenceTemplate")}`;
  confidenceText.dir = lang === "en" ? "ltr" : "rtl";
  confidenceFill.style.width = `${confidence}%`;
  confidenceFill.classList.toggle("low", confidence < 65);
  uncertaintyWarning.hidden = !payload.is_uncertain;
  demoBanner.hidden = !payload.is_demo;
  renderReferenceImages(payload.reference_images);
  audioNote.textContent = payload.tts_notice || payload.audio_notice || "";
  resultAudio.pause();
  resultAudio.removeAttribute("src");
  resultAudio.hidden = true;
  resultAudio.load();
  playAudioButton.hidden = true;

  if (payload.audio_url) {
    resultAudio.src = payload.audio_url;
    resultAudio.hidden = false;
    resultAudio.load();
    playResponseAudio();
  } else {
    audioNote.textContent = payload.tts_notice || t("audioUnavailable");
  }

  resultsCard.hidden = false;
  resultsCard.scrollIntoView({ behavior: "smooth", block: "start" });
}

playAudioButton.addEventListener("click", playResponseAudio);

newDiagnosisButton.addEventListener("click", () => {
  form.reset();
  selectedImage = null;
  recordedAudio = null;
  mediaRecorder = null;
  analyzeButton.disabled = true;
  imagePreview.hidden = true;
  imagePreview.removeAttribute("src");
  imageEmpty.hidden = false;
  imageName.hidden = true;
  clearReferenceImages();
  resultsCard.hidden = true;
  if (imageObjectUrl) URL.revokeObjectURL(imageObjectUrl);
  imageObjectUrl = null;
  setStatus(t("newStatus"), "", "newStatus");
  window.scrollTo({ top: 0, behavior: "smooth" });
});

initLanguage();
