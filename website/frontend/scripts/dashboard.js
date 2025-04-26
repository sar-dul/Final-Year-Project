const dropAreas = document.querySelectorAll('.drop-section')
const listSections = document.querySelectorAll('.list-section')
const listContainers = document.querySelectorAll('.list')
const fileSelectors = document.querySelectorAll('.file-selector')
const fileSelectorInputs = document.querySelectorAll('.file-selector-input')

// upload files with browse button for each container
fileSelectors.forEach((btn, index) => {
    btn.onclick = () => fileSelectorInputs[index].click()

    fileSelectorInputs[index].onchange = () => {
        [...fileSelectorInputs[index].files].forEach((file) => {
            if (typeValidation(file.type, file.name)) {
                uploadFile(file, listSections[index], listContainers[index])
            }
        })
    }
})

// handle drag & drop for each drop area
dropAreas.forEach((dropArea, index) => {
    dropArea.ondragover = (e) => {
        e.preventDefault();
        [...e.dataTransfer.items].forEach((item) => {
            if (typeValidation(item.type, item.name)) {
                dropArea.classList.add('drag-over-effect')
            }
        })
    }

    dropArea.ondragleave = () => {
        dropArea.classList.remove('drag-over-effect')
    }

    dropArea.ondrop = (e) => {
        e.preventDefault();
        dropArea.classList.remove('drag-over-effect')
        if (e.dataTransfer.items) {
            [...e.dataTransfer.items].forEach((item) => {
                if (item.kind === 'file') {
                    const file = item.getAsFile()
                    if (typeValidation(file.type, file.name)) {
                        uploadFile(file, listSections[index], listContainers[index])
                    }
                }
            })
        } else {
            [...e.dataTransfer.files].forEach((file) => {
                if (typeValidation(file.type, file.name)) {
                    uploadFile(file, listSections[index], listContainers[index])
                }
            })
        }
    }
})

// check the file type
function typeValidation(type, name){
    const splitType = type.split('/')[0];
    const extension = name.split('.').pop().toLowerCase();

    return (
        type === 'application/pdf' ||
        type === 'application/zip' ||
        type === 'text/x-python' ||
        extension === 'py' ||
        extension === 'ipynb' ||
        splitType === 'image' ||
        splitType === 'video'
    );
}

// select the icon for file type
function iconSelector(type) {
    const category = type.split('/')[0]
    if (type === 'application/pdf') return 'pdf.png'
    if (category === 'image') return 'image.png'
    if (category === 'video') return 'video.png'
    return 'file.png'
}

// upload file function
function uploadFile(file, listSection, listContainer) {
    listSection.style.display = 'block'
    const li = document.createElement('li')
    li.classList.add('in-prog')
    li.innerHTML = `
        <div class="col">
            <img src="icons/${iconSelector(file.type)}" alt="">
        </div>
        <div class="col">
            <div class="file-name">
                <div class="name">${file.name}</div>
                <span>0%</span>
            </div>
            <div class="file-progress">
                <span></span>
            </div>
            <div class="file-size">${(file.size / (1024 * 1024)).toFixed(2)} MB</div>
        </div>
        <div class="col">
            <svg xmlns="http://www.w3.org/2000/svg" class="cross" height="20" width="20"><path d="m5.979 14.917-.854-.896 4-4.021-4-4.062.854-.896 4.042 4.062 4-4.062.854.896-4 4.062 4 4.021-.854.896-4-4.063Z"/></svg>
            <svg xmlns="http://www.w3.org/2000/svg" class="tick" height="20" width="20"><path d="m8.229 14.438-3.896-3.917 1.438-1.438 2.458 2.459 6-6L15.667 7Z"/></svg>
        </div>
    `
    listContainer.prepend(li)

    const http = new XMLHttpRequest()
    const data = new FormData()
    data.append('file', file)

    http.onload = () => {
        li.classList.add('complete')
        li.classList.remove('in-prog')
    }

    http.upload.onprogress = (e) => {
        const percent_complete = (e.loaded / e.total) * 100
        li.querySelectorAll('span')[0].innerHTML = Math.round(percent_complete) + '%'
        li.querySelectorAll('span')[1].style.width = percent_complete + '%'
    }

    http.open('POST', 'sender.php', true)
    http.send(data)

    li.querySelector('.cross').onclick = () => http.abort()
    http.onabort = () => li.remove()
}

// find icon for file
function iconSelector(type){
    var splitType = (type.split('/')[0] == 'application') ? type.split('/')[1] : type.split('/')[0];
    return splitType + '.png'
}


function showSection(sectionId) {
    document.querySelectorAll('main').forEach(main => {
        if (['dashboard', 'upload', 'history'].includes(main.id)) {
            main.classList.remove('active');
        }
    });
    document.getElementById(sectionId).classList.add('active');
}


const allSideMenu = document.querySelectorAll('#sidebar .side-menu.top li a');

allSideMenu.forEach(item=> {
const li = item.parentElement;

item.addEventListener('click', function () {
allSideMenu.forEach(i=> {
    i.parentElement.classList.remove('active');
})
li.classList.add('active');
})
});


// TOGGLE SIDEBAR
const menuBar = document.querySelector('#content nav .bx.bx-menu');
const sidebar = document.getElementById('sidebar');

menuBar.addEventListener('click', function () {
sidebar.classList.toggle('hide');
})


const searchButton = document.querySelector('#content nav form .form-input button');
const searchButtonIcon = document.querySelector('#content nav form .form-input button .bx');
const searchForm = document.querySelector('#content nav form');

searchButton.addEventListener('click', function (e) {
if(window.innerWidth < 576) {
e.preventDefault();
searchForm.classList.toggle('show');
if(searchForm.classList.contains('show')) {
    searchButtonIcon.classList.replace('bx-search', 'bx-x');
} else {
    searchButtonIcon.classList.replace('bx-x', 'bx-search');
}
}
})


if(window.innerWidth < 768) {
sidebar.classList.add('hide');
} else if(window.innerWidth > 576) {
searchButtonIcon.classList.replace('bx-x', 'bx-search');
searchForm.classList.remove('show');
}


window.addEventListener('resize', function () {
if(this.innerWidth > 576) {
searchButtonIcon.classList.replace('bx-x', 'bx-search');
searchForm.classList.remove('show');
}
})


const switchMode = document.getElementById('switch-mode');

switchMode.addEventListener('change', function () {
if(this.checked) {
document.body.classList.add('dark');
} else {
document.body.classList.remove('dark');
}
})