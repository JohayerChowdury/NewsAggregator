// document.addEventListener("DOMContentLoaded", () => {
//   const apiUrl = "https://api.example.com/data"; // Replace with your API URL

//   fetch(apiUrl)
//     .then((response) => {
//       if (response.ok) {
//         return response.json();
//       } else {
//         throw new Error("Network response was not ok");
//       }
//     })
//     .then((data) => {
//       const container = document.getElementById("results-container");
//       data.forEach((item) => {
//         const div = document.createElement("div");
//         div.className = "result-item";
//         div.textContent = JSON.stringify(item); // Customize this to display the data as needed
//         container.appendChild(div);
//       });
//     })
//     .catch((error) => {
//       console.error("There was a problem with the fetch operation:", error);
//     });
// });

//   const addTodoButton = document.querySelector('[data-todo="add-todo"]');
//   const clearTodosButton = document.querySelector('[data-todo="clear-todos"]');
//   const empty = document.querySelector('[data-todo="empty"]');
//   const todo = document.querySelector('[data-todo="todo"]');
//   const todosParent = todo.parentNode;

//   let currentTodo = 0;

//   const addTodo = async () => {
//     try {
//       currentTodo++;
//       const data = await fetch(
//         `https://jsonplaceholder.typicode.com/todos/${currentTodo}`
//       );
//       const json = await data.json();
//       console.log(json);

//       const todos = [...document.querySelectorAll('[data-todo="todo"]')];
//       const newTodo = currentTodo === 1 ? todos[0] : todos[0].cloneNode(true);

//       const title = newTodo.querySelector('[data-todo="title"]');
//       const id = newTodo.querySelector('[data-todo="id"]');

//       title.innerText = `Title: ${json.title}`;
//       id.innerText = `ID: ${json.id}`;

//       if (currentTodo > 1) {
//         todosParent.appendChild(newTodo);
//       }
//       newTodo.style.display = 'flex';
// 			empty.style.display = 'none';
//       const removeButton = newTodo.querySelector('[data-todo="remove"]');
//       removeButton.addEventListener('click', () => {
//         const todos = [...document.querySelectorAll('[data-todo="todo"]')];
//         if (todos.length === 1) {
//           currentTodo = 0;
//           newTodo.style.display = 'none';
//           empty.style.display = 'block';
//         } else {
//           newTodo.parentNode.removeChild(newTodo);
//         }
//       });

//     } catch (err) {
//       console.error(`Error getting todo: ${err}`);
//     }
//   };

//   addTodoButton.addEventListener('click', addTodo);

//   const clearTodos = () => {
//     currentTodo = 0;
//     const todos = [...document.querySelectorAll('[data-todo="todo"]')];
//     todos.forEach((todo, index) => {
//       if (index === 0) {
//         todo.style.display = 'none';
//       } else {
//         todo.parentNode.removeChild(todo);
//       }
//     });
//     empty.style.display = 'none';
//   };

//   clearTodosButton.addEventListener('click', clearTodos);
