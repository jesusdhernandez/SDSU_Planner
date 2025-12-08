
async function api(path,opts){
    const r=await fetch(
        path,{headers:{'Content-Type':'application/json'},credentials:'same-origin',...opts}
    );
    if(!r.ok) throw new Error('HTTP Error '+r.status); 
    if (r.status===204){
        return null
    }
    else {
        return r.json();
    }
}

const cal = document.getElementById("calendar");
const cnt = document.getElementById("cnt")

// Days in each month (non-leap year)
const daysInMonth = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31];
const monthNames = ["January", "February", "March", "April", "May", "June", 
                    "July", "August", "September", "October", "November", "December"];

// Check if it's a leap year
function isLeapYear(year) {
    return (year % 4 === 0 && year % 100 !== 0) || (year % 400 === 0);
}

// Get days in a specific month
function getDaysInMonth(month, year) {
    if (month === 1 && isLeapYear(year)) { // February in leap year
        return 29;
    }
    return daysInMonth[month];
}

// Convert month and day to day number (1-365/366)
function monthDayToDayNumber(month, day, year) {
    year = year || new Date().getFullYear();
    let dayNumber = 0;
    
    // Add days from all previous months
    for (let i = 0; i < month; i++) {
        dayNumber += getDaysInMonth(i, year);
    }
    
    // Add days from current month
    dayNumber += day;
    
    return dayNumber;
}

// Generate calendar for the year
function generateCalendar() {
    const year = new Date().getFullYear();
    let dayCounter = 1;
    
    for (let month = 0; month < 12; month++) {
        const monthDiv = document.createElement("div");
        monthDiv.className = "month";
        monthDiv.id = `month-${month}`;
        
        const monthHeaderContainer = document.createElement("div");
        monthHeaderContainer.className = "month-header-container";
        
        const monthHeader = document.createElement("h2");
        monthHeader.textContent = `${monthNames[month]} ${year}`;
        monthHeaderContainer.appendChild(monthHeader);
        
        const goToTopBtn = document.createElement("button");
        goToTopBtn.className = "go-to-top-btn";
        goToTopBtn.textContent = "↑ Top";
        goToTopBtn.onclick = () => {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        };
        monthHeaderContainer.appendChild(goToTopBtn);
        
        monthDiv.appendChild(monthHeaderContainer);
        
        const daysDiv = document.createElement("div");
        daysDiv.className = "month-days";
        
        const daysInCurrentMonth = getDaysInMonth(month, year);
        
        for (let day = 1; day <= daysInCurrentMonth; day++) {
            const dayCell = document.createElement("div");
            dayCell.className = "day-cell";
            dayCell.id = String(dayCounter);
            dayCell.innerHTML = `<div class="day-number">${day}</div>`;
            daysDiv.appendChild(dayCell);
            dayCounter++;
        }
        
        monthDiv.appendChild(daysDiv);
        cal.appendChild(monthDiv);
    }
}

function dayCell(d){
    return document.getElementById(String(d))
}

//this function returns the list of the day and creates one if it doesn't exisist
function getList(day){
    let ul = day.querySelector("ul")
    if(!ul){
        ul = document.createElement("ul")
        day.appendChild(ul);
    }
    return ul;
}

//this function add a new list item to corresponding list
function addTaskToUI(task){
    let cell = dayCell(task.day)
    if(!cell){
        alert("Not a valid day!")
        return;
    }
    const ul = getList(cell)
    const li = document.createElement("li");
    li.id = `task-${task.id}`;
    li.textContent = `${task.number}. ${task.title}`;
    ul.appendChild(li);
}

async function displayTasks(){
    console.log("Started")
    const tasks = await api("/api/tasks", {method: "GET"});
    for(let i = 0; i< tasks.length; i++){
        addTaskToUI(tasks[i])
    }
}

function clear(){
    const cells = document.querySelectorAll(".day-cell ul");
    cells.forEach(ul => ul.remove());
}


//event is the submit event contains the type and data 
async function taskAdded(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const title = data.get("TaskName").toString().trim();
    const month = Number(data.get("AddMonth"));
    const dayOfMonth = Number(data.get("AddDay"));
    const day = monthDayToDayNumber(month, dayOfMonth);
    const number = Number(data.get("AddNumber"));

    const created = await api("/api/tasks", {method: "POST", body: JSON.stringify({title, day, number})})
    clear()
    displayTasks()
    cnt.textContent = String(Number(cnt.textContent)+1)
    event.target.reset();
}

async function taskDeleted(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const month = Number(data.get("DeleteMonth"));
    const dayOfMonth = Number(data.get("DeleteDay"));
    const day = monthDayToDayNumber(month, dayOfMonth);
    const number = Number(data.get("DeleteNumber"));
    
    const created = await api("/api/tasks", {method: "DELETE", body: JSON.stringify({day, number})})
    clear()
    displayTasks()
    cnt.textContent = String(Number(cnt.textContent)-1)
    event.target.reset();
}

async function taskModified(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    
    // Fields to find the task
    const originalMonth = Number(data.get("OriginalMonth"));
    const originalDayOfMonth = Number(data.get("OriginalDay"));
    const original_day = monthDayToDayNumber(originalMonth, originalDayOfMonth);
    const original_number = Number(data.get("OriginalNumber"));
    
    // New values (can be empty to keep original)
    const title = data.get("NewTask").toString().trim();
    
    let day = original_day;
    if (data.get("NewMonth") && data.get("NewDay")) {
        const newMonth = Number(data.get("NewMonth"));
        const newDayOfMonth = Number(data.get("NewDay"));
        day = monthDayToDayNumber(newMonth, newDayOfMonth);
    }
    
    const number = data.get("NewNumber") ? Number(data.get("NewNumber")) : original_number;
    
    console.log("Modify attempt with:", {original_day, original_number, title, day, number});
    
    try {
        const modified = await api("/api/tasks", {method: "PUT", body: JSON.stringify({original_day, original_number, title, day, number})})
        console.log("Modified response:", modified);
        clear()
        displayTasks()
        // Clear the form
        event.target.reset();
    } catch (error) {
        console.error("Error modifying task:", error);
        alert("Error modifying task: " + error.message);
    }
}



console.log("Successfully started!");
generateCalendar();
displayTasks();
document.getElementById("addTask").addEventListener("submit",taskAdded);
document.getElementById("deleteTask").addEventListener("submit",taskDeleted);
document.getElementById("modifyTask").addEventListener("submit",taskModified);

// Month navigation dropdown
document.getElementById("monthSelector").addEventListener("change", (e) => {
    const selectedMonth = e.target.value;
    if (selectedMonth !== "") {
        const monthElement = document.getElementById(`month-${selectedMonth}`);
        if (monthElement) {
            monthElement.scrollIntoView({ behavior: 'smooth', block: 'end' });
            e.target.value = ""; // Reset dropdown
        }
    }
});


