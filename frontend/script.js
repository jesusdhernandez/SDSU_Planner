
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

const cal = document.getElementById("calender");
const cnt = document.getElementById("cnt")

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
    for(let i = 0; i < 27; i++){
        if(cal.children[i].children[0]){
                    cal.children[i].children[0].remove()
        }
    }
}


//event is the submit event contains the type and data 
async function taskAdded(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const title = data.get("Task").toString().trim();
    const day = Number(data.get("Day"));
    const number = Number(data.get("Number"));

    const created = await api("/api/tasks", {method: "POST", body: JSON.stringify({title, day, number})})
    clear()
    displayTasks()
    cnt.textContent = String(Number(cnt.textContent)+1)
}

async function taskDeleted(event) {
    event.preventDefault();
    const data = new FormData(event.target);
    const title = data.get("Task").toString().trim();
    const day = Number(data.get("Day"));
    const number = Number(data.get("Number"));
    const created = await api("/api/tasks", {method: "DELETE", body: JSON.stringify({title, day, number})})
    clear()
    displayTasks()
    cnt.textContent = String(Number(cnt.textContent)-1)
}



console.log("sTARTED");
displayTasks();
document.getElementById("addTask").addEventListener("submit",taskAdded);
document.getElementById("deleteTask").addEventListener("submit",taskDeleted);


