const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const statusArea = document.getElementById('status-area');
const statusText = document.getElementById('status-text');
const loader = document.getElementById('loader');
const downloadBtn = document.getElementById('download-btn');
const resetBtn = document.getElementById('reset-btn');
const subtitle = document.querySelector('.subtitle');

// Trigger file input
dropZone.addEventListener('click', () => fileInput.click());

// Drag mechanics
dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
    dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length) handleFile(files[0]);
});

fileInput.addEventListener('change', (e) => {
    if (fileInput.files.length) handleFile(fileInput.files[0]);
});

async function handleFile(file) {
    if (!file.name.endsWith('.xlsx')) {
        alert("Please upload an Excel (.xlsx) file.");
        return;
    }

    // UI Reset
    statusArea.classList.remove('hidden');
    loader.classList.remove('hidden');
    downloadBtn.classList.add('hidden');
    resetBtn.classList.add('hidden');

    // Hide inputs while processing
    dropZone.classList.add('hidden');
    subtitle.classList.add('hidden');

    statusText.textContent = `Processing ${file.name}...`;
    statusText.style.color = 'var(--text-main)';

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch('/upload', {
            method: 'POST',
            body: formData
        });

        if (response.ok) {
            // Get filename from header or guess
            const contentDisposition = response.headers.get('content-disposition');
            let filename = `processed_${file.name}`;
            if (contentDisposition) {
                const match = contentDisposition.match(/filename="?(.+)"?/);
                if (match) filename = match[1];
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);

            // Success UI
            loader.classList.add('hidden');
            statusText.textContent = "Done! File saved.";
            statusText.style.color = '#15803d'; // green-700

            // Auto download logic
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            // We do NOT show the download button as requested, because it already downloaded.
            downloadBtn.classList.add('hidden');

            // Show reset button
            resetBtn.textContent = "Process Another File";
            resetBtn.classList.remove('hidden');

            resetBtn.onclick = () => {
                // Reset UI
                statusArea.classList.add('hidden');
                loader.classList.add('hidden');
                downloadBtn.classList.add('hidden');
                resetBtn.classList.add('hidden');
                fileInput.value = ''; // clear input

                // Show inputs again
                dropZone.classList.remove('hidden');
                subtitle.classList.remove('hidden');
            };

        } else {
            throw new Error("Server error");
        }
    } catch (error) {
        loader.classList.add('hidden');
        statusText.textContent = "Error processing file.";
        statusText.style.color = '#ef4444'; // red
        console.error(error);

        // Allow reset on error too
        resetBtn.textContent = "Try Again";
        resetBtn.classList.remove('hidden');
        resetBtn.onclick = () => {
            statusArea.classList.add('hidden');
            fileInput.value = '';
            dropZone.classList.remove('hidden');
            subtitle.classList.remove('hidden');
        };
    }
}

// --- Project Downloader Logic ---
const convertBtn = document.getElementById("convert-btn");
const projectUrlInput = document.getElementById("project-url");
const projectStatus = document.getElementById("project-status");
const projectStatusText = document.getElementById("project-status-text");

if (convertBtn) {
    convertBtn.addEventListener("click", () => {
        const url = projectUrlInput.value.trim();
        if (!url) {
            alert("Please enter a valid URL");
            return;
        }

        // UI Loading State
        projectStatus.classList.remove("hidden");
        projectStatusText.innerText = "Connecting to Nawy...";
        convertBtn.disabled = true;

        // Ensure progress bar exists and reset
        const progressBar = document.getElementById("project-progress-bar");
        if (progressBar) {
            progressBar.style.width = "0%";
            progressBar.style.backgroundColor = "#6c5ce7"; // Reset color
        }

        // Simulate Progress
        let progress = 0;
        const interval = setInterval(() => {
            if (progress < 90) {
                progress += Math.random() * 5;
                if (progressBar) progressBar.style.width = `${Math.min(progress, 90)}%`;

                if (progress > 10 && progress < 40) projectStatusText.innerText = "Scraping Project Data...";
                if (progress > 40 && progress < 70) projectStatusText.innerText = "Downloading High-Res Images...";
                if (progress > 70) projectStatusText.innerText = "Finalizing Archive...";
            }
        }, 800);

        fetch("/download-project", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ url: url })
        })
            .then(response => {
                if (response.ok) {
                    return response.blob();
                } else {
                    return response.json().then(err => { throw new Error(err.error || "Generation FAILED") });
                }
            })
            .then(blob => {
                clearInterval(interval);
                if (progressBar) progressBar.style.width = "100%";
                projectStatusText.innerText = "Done! Downloading...";

                // Create download link
                const downloadUrl = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.href = downloadUrl;
                // Revert to .zip to avoid "broken file" reports from OS tools that don't like mismatched extensions
                a.download = `project_files.zip`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
            })
            .catch(error => {
                clearInterval(interval);
                console.error("Error:", error);
                projectStatusText.innerText = `Error: ${error.message}`;
                if (progressBar) progressBar.style.backgroundColor = "#ff7675"; // Red for error
                alert(`Failed: ${error.message}`);
            })
            .finally(() => {
                convertBtn.disabled = false;
            });
    });
}
// --- View Switching Logic ---
const homeView = document.getElementById("home-view");
const excelView = document.getElementById("excel-tool-view");
const projectView = document.getElementById("project-tool-view");

const cardExcel = document.getElementById("card-excel");
const cardProject = document.getElementById("card-project");

const backExcel = document.getElementById("back-excel");
const backProject = document.getElementById("back-project");

function showView(view) {
    homeView.classList.add("hidden");
    excelView.classList.add("hidden");
    projectView.classList.add("hidden");

    view.classList.remove("hidden");
}

if (cardExcel) {
    cardExcel.addEventListener("click", () => showView(excelView));
}

if (cardProject) {
    cardProject.addEventListener("click", () => showView(projectView));
}

if (backExcel) {
    backExcel.addEventListener("click", () => showView(homeView));
}

if (backProject) {
    backProject.addEventListener("click", () => showView(homeView));
}
