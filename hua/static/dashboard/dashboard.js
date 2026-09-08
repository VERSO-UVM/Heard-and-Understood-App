// TODO: Organize
// TODO: Abstract some computation to helper functions
// TODO: Should csv reflect the pause data selected or all data?

const emotionalColor = 'green';
const invitationalColor = 'blue';
const nonConnectiveColor = 'yellow';

const canvasWidth = 500;
const canvasHeight = 300;

const numDataPoints = 75;
const canvasRectWidth = 3;

algorithmButton = document.getElementById("algorithm");
confusionMatrixButton = document.getElementById("confusionMatrix");
rawDataButton = document.getElementById("rawData");

recordingsInput = document.getElementById("recordingsInput");

modalPopup = document.getElementById("modalPopup");
background = document.getElementById("modalBackground");
modalContent = document.getElementById("modalContent");

emotionalCheckbox = document.getElementById("emotionalCheckbox");
invitationalCheckbox = document.getElementById("invitationalCheckbox");
nonConnectiveCheckbox = document.getElementById("non-connectiveCheckbox");
accuracyToggle = document.getElementById("accuracyToggle");

showEmotional = true;
showInvitational = true;
showNonConnective = true;
showAccuracy = true;

recordingVal = '';

emotionalPauses = [];
invitationalPauses = [];
nonConnectivePauses = [];

downloadButton = document.getElementById("downloadCSV");

interactiveElements = [algorithmButton, confusionMatrixButton, rawDataButton, emotionalCheckbox, invitationalCheckbox, nonConnectiveCheckbox, downloadButton, accuracyToggle];

recordings = [];

fetch('/api/uploads')
    .then(response => response.json())
    .then(files => {
        recordings = files;
        var optionsHTML = '<option value="" disabled selected>Select a recording</option>';
        for (i = 0; i < recordings.length; ++i) {
            optionsHTML += '<option value="' + recordings[i] + '">' + recordings[i] + '</option>';
        }
        recordingsInput.innerHTML = optionsHTML;
    })
    .catch(error => console.error('Error loading uploads:', error));

confusionMatrixButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.textContent = confusionMatrixButton.value + " for " + recordingVal;
    if(showAccuracy){
        modalContent.textContent += " with 96% accuracy";
    }
}
rawDataButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.innerHTML = "Loading raw data...";

    fetch('/api/consert_output')
        .then(response => {
            if (!response.ok) {
                throw new Error('No output available yet - run the algorithm first.');
            }
            return response.json();
        })
        .then(data => {
            let tableHTML = '<table border="1" style="margin: auto; text-align: left;"><thead><tr>';
            data.columns.forEach(col => {
                tableHTML += '<th>' + col + '</th>';
            });
            tableHTML += '</tr></thead><tbody>';
            data.rows.forEach(row => {
                tableHTML += '<tr>';
                data.columns.forEach(col => {
                    tableHTML += '<td>' + row[col] + '</td>';
                });
                tableHTML += '</tr>';
            });
            tableHTML += '</tbody></table>';
            modalContent.innerHTML = tableHTML;
        })
        .catch(error => {
            modalContent.textContent = error.message;
        });
}

recordingsInput.addEventListener("change", function(){
    recordingVal = this.value;
    if (recordings.includes(recordingVal)) {
        algorithmButton.disabled = false;
    } else {
        algorithmButton.disabled = true;
    }
});

emotionalCheckbox.addEventListener("input", function(){
    showEmotional = !showEmotional;
    currentlyVisiblePauses();
    isolateData();
});
invitationalCheckbox.addEventListener("input", function(){
    showInvitational = !showInvitational;
    currentlyVisiblePauses();
    isolateData();
});
nonConnectiveCheckbox.addEventListener("input", function(){
    showNonConnective = !showNonConnective;
    currentlyVisiblePauses();
    isolateData();
});
accuracyToggle.addEventListener("input", function(){
    showAccuracy = !showAccuracy;
    if(showAccuracy){
        console.log("Showing accuracy");
    }
})

// Only for showing that the values are kept track of temporarily
currentlyVisiblePauses = function() {
    if(showEmotional){
        console.log("Showing Emotional Pauses");
    }
    if(showInvitational){
        console.log("Showing Invitational Pauses");
    }
    if(showNonConnective){
        console.log("Showing Non-Connective Pauses");
    }
}

downloadButton.onclick = function() {
    window.location.href = '/download_consert_csv';
}

window.onclick = function(event) {
    if (event.target == background) {
        modalPopup.style.display = "none";
        background.style.display = "none";
    }
}

function downloadToCSV() {
    if (recordingVal != '') {
        try {
            // This would be the filepath once we can access directory in exe possibly?
            // let filePath = '../downloadedData/' + recordingVal + '.csv';
            let filePath = recordingVal + '.csv';
            let csvText = generateCSVText();
            const a = document.createElement('a');
            const file = new Blob([csvText], { type: "text/plain" });
            a.href = URL.createObjectURL(file);
            a.download = filePath;
            a.click();
            URL.revokeObjectURL(a.href);

        } catch(error) {
            console.log("Erorr downloading CSV for " + recordingVal)
        }
    }
}

function runAlgorithm() {
    clearCanvas();
    emotionalPauses = [];
    invitationalPauses = [];
    nonConnectivePauses = [];

    console.log("simulating algorithm...");
    populateGraph();
    interactiveElements.forEach(button=> {
        button.disabled = false;
    })
}

function generateCSVText() {
    let dummyData = ['100101011', '10100101', '1000001000'];
    var returnString = '';
    for (i = 0; i < dummyData.length; ++i) {
        returnString += dummyData[i];
    }
    return returnString;
}

function populateGraph() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    // Emotional pause data
    ctx.fillStyle = emotionalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showEmotional){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        emotionalPauses.push(randomX);
    }
    // Invitational pause data
    ctx.fillStyle = invitationalColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showInvitational){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        invitationalPauses.push(randomX);
    }
    // Non-connective pause data
    ctx.fillStyle = nonConnectiveColor;
    for (i = 0; i < numDataPoints; ++i) {
        randomX = getRandomNumber(1, canvasWidth);
        if(showNonConnective){
            ctx.fillRect(randomX, 0, canvasRectWidth,canvasHeight);
        }
        nonConnectivePauses.push(randomX);
    }
}

function resetPage() {
    clearCanvas()
    emotionalPauses = [];
    invitationalPauses = [];
    nonConnectivePauses = [];
    recordingsInput.value = '';
    interactiveElements.forEach(button=> {
        button.disabled = true;
    })
}

function clearCanvas() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, canvas.width, canvas.height);
}

function isolateData() {
    const canvas = document.getElementById("myCanvas");
    const ctx = canvas.getContext("2d");
    clearCanvas()
    if(showEmotional) {
        ctx.fillStyle = emotionalColor;
        for(i = 0; i < emotionalPauses.length; ++i) {
            ctx.fillRect(emotionalPauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
    if(showInvitational) {
        ctx.fillStyle = invitationalColor;
        for(i = 0; i < invitationalPauses.length; ++i) {
            ctx.fillRect(invitationalPauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
    if(showNonConnective) {
        ctx.fillStyle = nonConnectiveColor;
        for(i = 0; i < nonConnectivePauses.length; ++i) {
            ctx.fillRect(nonConnectivePauses[i], 0, canvasRectWidth, canvasHeight);
        }
    }
}

function getRandomNumber(min, max) {
    return Math.random() * (max - min) + min;
  }