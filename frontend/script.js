
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
let lastAction = null; // store last action for undo

function updateUndoUI(){
    const btn = document.getElementById('undo-btn');
    if(!btn) return;
    if(lastAction){
        btn.disabled = false;
        btn.title = `Undo last action: ${lastAction.type}`;
    } else {
        btn.disabled = true;
        btn.title = 'Nothing to undo';
    }
}

async function undoLastAction(){
    if(!lastAction) return;
    const action = lastAction;
    lastAction = null; // clear early to prevent re-entrancy
    updateUndoUI();
    try{
        if(action.type === 'add'){
            const t = action.task;
            await api('/api/tasks', { method: 'DELETE', body: JSON.stringify({ day: t.day, number: t.number }) });
            await displayTasks();
            alert('Undid add');
        } else if(action.type === 'delete'){
            const t = action.task;
            await api('/api/tasks', { method: 'POST', body: JSON.stringify({ title: t.title, day: t.day, number: t.number }) });
            await displayTasks();
            alert('Undid delete');
        } else if(action.type === 'modify'){
            const orig = action.original;
            const upd = action.updated;
            if(!upd){
                alert('Cannot undo: updated task info missing');
                return;
            }
            // revert: find current task by its updated day/number
            const payload = {
                original_day: Number(upd.day),
                original_number: Number(upd.number),
                title: orig ? orig.title : upd.title,
                day: orig ? Number(orig.day) : Number(upd.day),
                number: orig ? Number(orig.number) : Number(upd.number)
            };
            await api('/api/tasks', { method: 'PUT', body: JSON.stringify(payload) });
            await displayTasks();
            alert('Undid modify');
        } else if(action.type === 'clear_month' || action.type === 'clear_all'){
            const tasks = action.tasks || [];
            let restored = 0;
            for(const t of tasks){
                try{
                    await api('/api/tasks', { method: 'POST', body: JSON.stringify({ title: t.title, day: t.day, number: t.number }) });
                    restored++;
                }catch(e){
                    // ignore individual failures
                }
            }
            await displayTasks();
            alert(`Undid ${action.type}: restored ${restored} tasks`);
        }
    }catch(e){
        console.error('Undo failed', e);
        alert('Undo failed: ' + (e.message || e));
    } finally {
        lastAction = null;
        updateUndoUI();
    }
}

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

            // Clear this month button
            const clearMonthBtn = document.createElement("button");
            clearMonthBtn.className = "clear-month-btn";
            clearMonthBtn.textContent = "Clear Month";
            clearMonthBtn.onclick = async () => {
                if (!confirm(`Clear all tasks for ${monthNames[month]}? This cannot be undone.`)) return;
                try {
                    const res = await api(`/api/tasks/month/${month}`, { method: 'DELETE' });
                    console.log('clear month', res);
                    // record last action for undo
                    lastAction = { type: 'clear_month', month: month, tasks: res.tasks || [] };
                    updateUndoUI();
                    clear();
                    await displayTasks();
                    alert(`Deleted ${res.deleted} tasks from ${monthNames[month]}.`);
                } catch (err) {
                    console.error(err);
                    alert('Failed to clear month: ' + err.message);
                }
            };
            monthHeaderContainer.appendChild(clearMonthBtn);

            // Note: a single global "Clear All" button is provided in the top month-nav.
        
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
    // clear existing UI then render fresh
    clear();
    if (typeof cnt !== 'undefined' && cnt) cnt.textContent = String(tasks.length);
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
    let number = Number(data.get("AddNumber"));

    // If number is missing/invalid, pick next free slot for that day
    if (!Number.isInteger(number) || number <= 0) {
        const all = await api('/api/tasks', { method: 'GET' });
        let max = 0;
        for (const t of all) {
            if (Number(t.day) === day) {
                const n = Number(t.number) || 0;
                if (n > max) max = n;
            }
        }
        number = max + 1;
    }

    const created = await api("/api/tasks", {method: "POST", body: JSON.stringify({title, day, number})})
    // record for undo
    lastAction = { type: 'add', task: created };
    updateUndoUI();
    clear()
    await displayTasks()
    event.target.reset();
}

async function taskDeleted(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const month = Number(data.get("DeleteMonth"));
    const dayOfMonth = Number(data.get("DeleteDay"));
    const day = monthDayToDayNumber(month, dayOfMonth);
    const number = Number(data.get("DeleteNumber"));
    const deleted = await api("/api/tasks", {method: "DELETE", body: JSON.stringify({day, number})})
    // backend returns deleted task
    lastAction = { type: 'delete', task: deleted };
    updateUndoUI();
    clear()
    await displayTasks()
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
    
    // Handle new day calculation - use original values if new ones aren't provided
    let newMonth = data.get("NewMonth") !== "" ? Number(data.get("NewMonth")) : originalMonth;
    let newDayOfMonth = data.get("NewDay") ? Number(data.get("NewDay")) : originalDayOfMonth;
    const day = monthDayToDayNumber(newMonth, newDayOfMonth);
    
    const number = data.get("NewNumber") ? Number(data.get("NewNumber")) : original_number;
    
    console.log("Modify attempt with:", {original_day, original_number, title, day, number});
    
    try {
        // fetch original task for undo
        const all = await api('/api/tasks', { method: 'GET' });
        const originalTask = all.find(t => Number(t.day) === original_day && Number(t.number) === original_number) || null;

        const modified = await api("/api/tasks", {method: "PUT", body: JSON.stringify({original_day, original_number, title, day, number})})
        console.log("Modified response:", modified);
        lastAction = { type: 'modify', original: originalTask, updated: modified };
        updateUndoUI();
        clear()
        await displayTasks()
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

// Add a single Clear All button to the month-nav area (right side)
;(function addGlobalClearAll(){
    const nav = document.getElementById('month-nav');
    if(!nav) return;
    const undoBtn = document.createElement('button');
    undoBtn.id = 'undo-btn';
    undoBtn.className = 'global-undo-btn';
    undoBtn.textContent = 'Undo';
    undoBtn.disabled = true;
    undoBtn.onclick = undoLastAction;
    nav.appendChild(undoBtn);

    const btn = document.createElement('button');
    btn.className = 'clear-all-btn';
    btn.textContent = 'Clear All';
    btn.onclick = async () => {
        if(!confirm('Clear ALL tasks for the entire year? This cannot be undone.')) return;
        try{
            const res = await api('/api/tasks/clear_all', { method: 'DELETE' });
            console.log('clear all', res);
            // record last action for undo
            lastAction = { type: 'clear_all', tasks: res.tasks || [] };
            updateUndoUI();
            clear();
            await displayTasks();
            alert(`Deleted ${res.deleted} tasks from the calendar.`);
        } catch (err){
            console.error(err);
            alert('Failed to clear all: ' + err.message);
        }
    };
    // place to the right in the flex container
    btn.style.marginLeft = 'auto';
    nav.appendChild(btn);
})();

// initialize undo UI state
updateUndoUI();


