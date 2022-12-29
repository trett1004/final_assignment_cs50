function check_me(input_id) {
    var checked_input = document.querySelector("input[id=" + input_id + "]");
    var checked_label = document.querySelector("label[name=" + input_id + "]");

    if (checked_input.checked){
        checked_label.style.textDecoration = "line-through";
    }
    else {
        checked_label.style.textDecoration = "";
    }

    var btn = document.getElementById("btn_remove");
    btn.value = "REMOVE ITEMS";
    btn.style.color = "#FFFFFF";
    btn.style.backgroundColor = "#FF0000";
}

function selected(item) {
    return item == "Milch"
}

function select_item(item) {
    console.info(item)
    console.info("i ran 1")
}