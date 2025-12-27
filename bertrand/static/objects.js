'use strict';

// INITIALIZE VARIABLES
const uploadButton = document.getElementById('uploadButton');
const fileInput = document.getElementById('fileInput');
const textInput = document.getElementById('textInput');
const uploadStatus = document.getElementById('message');

// LOGIC CALCULATOR
uploadButton.addEventListener('click', async () => {
    if (textInput.value.trim() !== "") {
        try {
            const formData = new FormData();
            formData.append('textInput', textInput.value);

            // Proceed to analysis
            const analysisResponse = await fetch('/analysis', {
                method: 'POST',
                body: formData,
            });

            // Receive the results of analysis
            let analysisResult;
            try {
              analysisResult = await analysisResponse.json();
            } catch {
              const text = await analysisResponse.text();
              analysisResult = { success: analysisResponse.ok, message: text };
            }
            
            if (analysisResult.success) {
              const conclusion = analysisResult.conclusion;
            
              // Pretty-print only objects/arrays; strings shown verbatim
              const shown =
                conclusion && typeof conclusion === "object"
                  ? JSON.stringify(conclusion, null, 2)
                  : String(conclusion ?? "");
            
              document.getElementById("reportContent").innerText = shown;
              uploadStatus.innerText = analysisResult.message || "No compile-time errors.";
            } else {
              // Errors as plain text
              const err =
                (analysisResult.error && (analysisResult.error.message || 
                    analysisResult.error)) ||
                    analysisResult.message ||
                    analysisResult.conclusion ||
                    "Analysis failed.";
            
              document.getElementById("reportContent").innerText = 
                String(err ?? "");
              uploadStatus.innerText = analysisResult.message || 
                "Run-time analysis failed.";
                uploadStatus.style.color = "red";

            }

        } catch (error) {
            console.error("Error:", error);
            uploadStatus.innerText = "Runtime error occurred.";
            uploadStatus.style.color = "red";

        }
    } else {
        fileInput.click();
    }
});

// FILE UPLOADER
fileInput.addEventListener('change', async function(event) {
    const file = event.target.files[0];
    if (file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('/upload', 
                { method: 'POST', body: formData });
            const result = await response.json();
            
            if (result.success) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    textInput.value = e.target.result;
                };
                reader.readAsText(file);
                uploadStatus.innerText = result.message || 
                    "File uploaded successfully.";
            } else {
                uploadStatus.innerText = result.message || 
                    "File upload failed.";
                    uploadStatus.style.color = "red";
            }
        } catch (error) {
            uploadStatus.innerText = "Error uploading file.";
            uploadStatus.style.color = "red";
        }
    }
});

// TEXT DOWNLOADER
function saveText(buttonId, getTextContentCallback) {
    const button = document.getElementById(buttonId);

    button.addEventListener('click', () => {
        const textContent = getTextContentCallback().trim();

        if (!textContent) {
            uploadStatus.innerText = "There is no text to save.";
            uploadStatus.style.color = "red";
            return;
        }

        fetch('/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `textInput=${encodeURIComponent(textContent)}`
        })

            .then((response) => response.blob())
            .then((blob) => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'downloaded_text.txt'; 
                // File name for the downloaded text file
                document.body.appendChild(a);
                a.click();
                a.remove();
                window.URL.revokeObjectURL(url);
            })
            .catch((error) => {
                console.error('Error:', error);
                uploadStatus.innerText = "An error occurred while " +
                    "saving the text.";
                uploadStatus.style.color = "red";
            });
    });
}

// INITIALIZE DOWNLOAD BUTTONS AND CALL THE FUNCTION
saveText('saveInput', () => document.getElementById('textInput').value);
saveText('saveOutput', () => document.getElementById('reportContent').innerText);

// RESET APPLICATION AND CLEAR WINDOWS
function clearOutput() {
    const currentUrl = location.href;
    window.location.assign(currentUrl);
}

// SCREEN RESIZING
function toggleFullScreen() {
    const button = document.getElementById('fullscreenButton');
    const elem = document.documentElement;

    if (!document.fullscreenElement) {
        elem.requestFullscreen();
        button.textContent = 'Exit Full Screen';
    } else {
        document.exitFullscreen();
        button.textContent = 'Full Screen';
    }
}

// CALL THE SCREEN RESIZE FUNCTION
document.addEventListener('fullscreenchange', () => {
    const button = document.getElementById('fullscreenButton');
    button.textContent = document.fullscreenElement 
        ? 'Exit Full Screen' : 'Full Screen';
});

// TEXT INPUT WINDOW PLACEHOLDER
textInput.placeholder =
    "THIS IS THE CALCULATOR INPUT WINDOW." +
    "Type your script here and press the 'Upload Text / Calculate' button " +
    "below to load and calculate it on our website. If you instead want to " +
    "upload text from a text file, with an empty input window press the same " +
    "button to upload the file's contents and then, once these are loaded " + 
    "into the text input window, press this button a second time to " +
    "calculate. We will not keep any user input or uploaded text after it " + 
    "has been loaded into and calculated on our website. " +
    "Click on the input window and then press any key to automatically " +
    "insert a number at the beginning of each " +
    "line. A period must terminate the last expression entered. All statements " +
    "are terminated by typing a semicolon or entering a new line. " +
    "For further instructions, see the 'Lexicon' link at the top of the left " +
    "window. File upload size is limited to 1 MB.";

// Insert a single logic/set theory character from the UTF-8 lexicon buttons
function insertAtCursor(charToInsert) {
    let cursorStart = textInput.selectionStart;
    let cursorEnd = textInput.selectionEnd;
    let textValue = textInput.value;

    // If this is the first thing inserted (e.g., lexicon button click),
    // seed the first line header so renumberLines doesn't shift the caret into the prefix.
    if (textValue.trim() === '') {
        lineCount = 1;
        const lineHeader = `${lineCount}.  `;
        textInput.value = lineHeader;
        textValue = lineHeader;
        cursorStart = cursorEnd = lineHeader.length;
        firstKeyPressed = true;
    }

    // Mirror processTextInput(): insert a trailing space for non-whitespace tokens
    const textToInsert =
        (charToInsert && typeof charToInsert === 'string' && !/\s/.test(charToInsert))
            ? (charToInsert + ' ')
            : charToInsert;

    // Insert at the cursor position
    textInput.value =
        textValue.substring(0, cursorStart) +
        textToInsert +
        textValue.substring(cursorEnd);

    // Cursor ends after inserted text + (possible) space
    textInput.selectionStart = textInput.selectionEnd = cursorStart +
        textToInsert.length;

    // Keep line numbers synced for programmatic inserts
    if (!isRenumbering) {
        renumberLines();
    }

    textInput.focus();
}

// Insert a UTF-8 logic character after entering a three character abbreviation
function replaceTextAtCursor(text, start, end) {
    const textValue = textInput.value;
    textInput.value = textValue.substring(0, start) + text + 
        textValue.substring(end);
    textInput.selectionStart = textInput.selectionEnd = start + text.length;
    textInput.focus();
}

// Call the replaceTextAtCursor function
function processTextInput() {
    const lexicon = {
        "nul": "∅", "con": "∧", "dis": "∨", /*"sum": "Σ",*/ "imp": "→",
        "iff": "↔", "exd": "⨁", "nor": "↓", "nan": "↑", /*"dom": "𝔇",
        "ran": "ℛ",*/ "eqv": "≡", "ttt": "⊤", "fff": "⊥", "not": "¬",
        "eee": "∃", "all": "∀", "mem": "∈", /*"inc": "⊆", "src": "⊂",
        "int": "∩", "uni": "∪", "sym": "∆",*/ "phi": "φ", "Phi": "ϕ",
        "psi": "ψ", /*"PPP": "𝒫", "xxx": "×", "fld": "ℱ", "idt": "ℐ", "cir": "⚬"*/
    };

    const cursorPosition = textInput.selectionStart;
    const value = textInput.value;

    if (cursorPosition > 0 && /\s/.test(value.charAt(cursorPosition - 1))) {
        const lastWhitespaceIndex = value.lastIndexOf(' ', cursorPosition - 2);
        const currentChunk = value.substring(lastWhitespaceIndex + 1, 
            cursorPosition - 1);
        if (currentChunk.length === 3 && lexicon[currentChunk]) {
            replaceTextAtCursor(lexicon[currentChunk] + ' ', 
            lastWhitespaceIndex + 1, cursorPosition);
        }
    }
}

// Call the processTextInput function
textInput.addEventListener('input', (event) => {
    if (event.inputType === 'insertText' && event.data === ' ') {
        processTextInput();
    }
});

// LINE NUMBERING AND PROTECTION
function getCurrentLineStart(text, pos) {
    return text.lastIndexOf('\n', pos - 1) + 1;
}

// Return the end index of the protected "N.  " prefix (line number + dot + two spaces)
function getProtectedPrefixEnd(text, lineStart) {
    const lineEndIndex = text.indexOf('\n', lineStart);
    const lineEnd = lineEndIndex === -1 ? text.length : lineEndIndex;
    const lineText = text.slice(lineStart, lineEnd);

    const m = lineText.match(/^(\d+)\.\s\s/);
    if (!m) {
        return lineStart; // nothing to protect
    }
    return lineStart + m[0].length;
}

// Return the start/end indexes of the protected space prefix
// (the spaces after the "N." part) on a given line.
function getProtectedRange(text, lineStart) {
    const lineEndIndex = text.indexOf('\n', lineStart);
    const lineEnd = lineEndIndex === -1 ? text.length : lineEndIndex;
    const lineText = text.slice(lineStart, lineEnd);

    const dotIndex = lineText.indexOf('.');
    if (dotIndex === -1) {
        // No "N." prefix found, nothing to protect
        return { protectedStart: lineEnd, protectedEnd: lineEnd };
    }

    // Spaces immediately after the dot are protected
    const protectedStart = lineStart + dotIndex + 1;
    let i = protectedStart;
    while (i < text.length && text[i] === ' ') {
        i++;
    }
    return { protectedStart, protectedEnd: i };
}

// Initialize Line Numbering Variables
let lineCount = 1;
let firstKeyPressed = false;
let renumberPending = false;
let isRenumbering = false;
let renumberTimer = null;

// Line renumbering function
function renumberLines() {
    isRenumbering = true;

    const text = textInput.value;
    const cursorPos = textInput.selectionStart;
    const selectionEnd = textInput.selectionEnd;

    // Figure out current cursor line/column
    function getLineAndColumn(pos) {
        const before = text.slice(0, pos);
        const parts = before.split('\n');
        const lineIndex = parts.length - 1;
        const column = parts[parts.length - 1].length;
        return { lineIndex, column };
    }

    const cursorLC = getLineAndColumn(cursorPos);
    const selEndLC = getLineAndColumn(selectionEnd);

    const lines = text.split('\n');
    const newLines = [];

    for (let i = 0; i < lines.length; i++) {
        const line = lines[i];
        let rest = line;

        // Strip any existing "N.  " style prefix
        const m = line.match(/^(\d+)\.\s\s(.*)$/);
        if (m) {
            rest = m[2];
        }

        newLines.push(`${i + 1}.  ${rest}`);
    }

    const newText = newLines.join('\n');

    function posFromLineCol(linesArr, lineIndex, column) {
        if (lineIndex < 0) return 0;
        if (lineIndex >= linesArr.length) {
            lineIndex = linesArr.length - 1;
        }

        let pos = 0;
        for (let i = 0; i < lineIndex; i++) {
            // +1 for newline between lines
            pos += linesArr[i].length + 1;
        }

        const line = linesArr[lineIndex] || '';
        const clampedCol = Math.min(column, line.length);
        return pos + clampedCol;
    }

    const newCursorPos = posFromLineCol(newLines, cursorLC.lineIndex, cursorLC.column);
    const newSelectionEnd = posFromLineCol(newLines, selEndLC.lineIndex, selEndLC.column);

    textInput.value = newText;
    textInput.selectionStart = newCursorPos;
    textInput.selectionEnd = newSelectionEnd;

    // Keep the next line number consistent
    lineCount = newLines.length;

    isRenumbering = false;
}

// MASTER TEXT INPUT FUNCTION
textInput.addEventListener('keydown', function (event) {
    const cursorPos = textInput.selectionStart;
    const selectionEnd = textInput.selectionEnd;
    const text = textInput.value;

    // Any keydown: schedule a renumber (after the keystroke is applied)
    renumberPending = true;

    if (renumberTimer !== null) {
        clearTimeout(renumberTimer);
    }

    renumberTimer = setTimeout(() => {
        renumberTimer = null;

        if (isRenumbering) {
            return;
        }
        if (renumberPending) {
            renumberPending = false;
            renumberLines();
        }
    }, 0);


    if (event.key === 'Tab') {
        event.preventDefault();
        insertAtCursor('\t');
        return;
    }

    // ArrowLeft: don't allow moving into the protected "N.  " prefix
    if (event.key === 'ArrowLeft') {
        const lineStart = getCurrentLineStart(text, cursorPos);
        const prefixEnd = getProtectedPrefixEnd(text, lineStart);
    
        // If there's no selection, ArrowLeft would move to cursorPos - 1.
        // If there is a selection, ArrowLeft collapses to selectionStart (cursorPos).
        const wouldGoTo = (cursorPos === selectionEnd) ? (cursorPos - 1) : cursorPos;
    
        if (wouldGoTo < prefixEnd) {
            event.preventDefault();
            textInput.selectionStart = textInput.selectionEnd = prefixEnd;
            return;
        }
    }

    // Backspace/Delete: protect the ".  " spaces and schedule renumbering
    if (event.key === 'Backspace' || event.key === 'Delete') {
        const lineStart = getCurrentLineStart(text, cursorPos);
        const { protectedStart, protectedEnd } = getProtectedRange(text, lineStart);

        if (event.key === 'Backspace') {
            if (cursorPos === selectionEnd) {
                const deleteIndex = cursorPos - 1;
                if (deleteIndex >= protectedStart && deleteIndex < protectedEnd) {
                    event.preventDefault();
                    return;
                }
            } else {
                if (selectionEnd > protectedStart && cursorPos < protectedEnd) {
                    event.preventDefault();
                    return;
                }
            }
        } else if (event.key === 'Delete') {
            if (cursorPos === selectionEnd) {
                const deleteIndex = cursorPos;
                if (deleteIndex >= protectedStart && deleteIndex < protectedEnd) {
                    event.preventDefault();
                    return;
                }
            } else {
                if (selectionEnd > protectedStart && cursorPos < protectedEnd) {
                    event.preventDefault();
                    return;
                }
            }
        }

        // If we get here, deletion is allowed.
        // Check whether it will remove any newline(s); if so, renumber afterward.
        if (cursorPos !== selectionEnd) {
            const selectionText = text.slice(cursorPos, selectionEnd);
            if (selectionText.includes('\n')) {
                renumberPending = true;
            }
        } else {
            let deleteIndex;
            if (event.key === 'Backspace') {
                deleteIndex = cursorPos - 1;
            } else {
                deleteIndex = cursorPos;
            }
            if (deleteIndex >= 0 && deleteIndex < text.length && text[deleteIndex] === '\n') {
                renumberPending = true;
            }
        }
    }

    // First keystroke: insert "1.  "
    if (!firstKeyPressed && text.trim() === '') {
        const lineHeader = `${lineCount}.  `;
        textInput.value = lineHeader;
        textInput.selectionStart = textInput.selectionEnd = lineHeader.length;
        firstKeyPressed = true;
        event.preventDefault();
        return;
    }

    // Enter: new line with next number + renumber all lines
    if (event.key === 'Enter') {
        event.preventDefault();
        lineCount++;
        insertAtCursor(`\n${lineCount}.  `);
        return;
    }
});

// After the browser has applied a deletion that we flagged, renumber lines.
textInput.addEventListener('input', () => {
    if (isRenumbering) {
        return;
    }
    if (renumberPending) {
        renumberPending = false;
        renumberLines();
    }
});
