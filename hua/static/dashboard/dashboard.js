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

recordingsList = document.getElementById("recordings");
recordingsInput = document.getElementById("recordingsInput");

projectsList = document.getElementById("projects");
projectsInput = document.getElementById("projectsInput");

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
projectVal = '';

// Arrays of dummy pause data in graph
emotionalPauses = [];
invitationalPauses = [];
nonConnectivePauses = [];

downloadButton = document.getElementById("downloadCSV");

interactiveElements = [algorithmButton, confusionMatrixButton, rawDataButton, emotionalCheckbox, invitationalCheckbox, nonConnectiveCheckbox, downloadButton, accuracyToggle];

recordings = ["recording 1", "recording 2", "recording 3", "recording 4"];
var optionsText = '';
for(i = 0; i < recordings.length; ++i) {
    optionsText += '<option value="' + recordings[i] + '" />';
}
recordingsList.innerHTML = optionsText;

projects = ["Vermont Conversation Lab", "Project 2", "Project 3", "Project 4"];
var projectsOptions = '';
for(i = 0; i < projects.length; ++i) {
    projectsOptions += '<option value="' + projects[i] + '" />';
}
projectsList.innerHTML = projectsOptions;

confusionMatrixButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.textContent = confusionMatrixButton.value + " for " + recordingVal;
    if(showAccuracy){
        // Hard coded accuracy until we get actual data
        modalContent.textContent += " with 96% accuracy";
    }
}
rawDataButton.onclick = function() {
    modalPopup.style.display = "block";
    background.style.display = "block";
    modalContent.textContent = rawDataButton.value + " for " + recordingVal;
}
projectsInput.addEventListener("input", function(){
    projectVal = this.value;
    if(projects.includes(projectVal)) {
        recordingsInput.disabled = false;
    } else {
        recordingsInput.disabled = true;
        resetPage();
    }
})

recordingsInput.addEventListener("input", function(){
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

downloadCSV = function() {
    if(recordingVal != ''){
        console.log('downloading csv for ' + recordingVal);
    }
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
    // Clear the entire canvas
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
