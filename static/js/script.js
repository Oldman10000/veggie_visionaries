$(document).ready(function () {

    // Dynamic input function taken and adapted from https://www.codexworld.com/add-remove-input-fields-dynamically-using-jquery/
    const maxFieldIngredients = 15; //Input fields increment limitation
    const maxFieldInstructions = 10; //Input fields increment limitation
    let ingredientInputs = $(".ingredient").length; //Initial field counter is amount of nodes
    let instructionInputs = $(".instruction").length; //Initial field counter is amount of nodes

    //Once add button is clicked
    $(".add_ingredient_button").click(function () {
        //Check maximum number of input fields
        if (ingredientInputs < maxFieldIngredients) {
            ingredientInputs++; //Increment field counter
            $('.ingredient_field_wrapper').append(`
            <div class="form-outline form-white mb-4">
                <input type="text" name="ingredient" id="ingredient${ingredientInputs}" class="form-control ingredient" required />
                <label class="form-label" for="ingredient${ingredientInputs}">Ingredient</label>
                <a href="javascript:void(0);" class="remove_button" title="Add field"><i class="fas fa-minus"></i></a>
            </div>
            `)
            ingredientInputs = $(".ingredient").length;
            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                new mdb.Input(formOutline).init();
            });
        }
    });

    //Once add button is clicked
    $(".add_instruction_button").click(function () {
        //Check maximum number of input fields
        if (instructionInputs < maxFieldInstructions) {
            instructionInputs++; //Increment field counter
            $('.instruction_field_wrapper').append(`
            <div class="form-outline form-white mb-4">
                <textarea name="instruction" id="instruction${instructionInputs}" class="form-control instruction" rows=4 required></textarea>
                <label class="form-label" for="instruction${instructionInputs}">Instruction ${instructionInputs}</label>
            </div>
            `)
            instructionInputs = $(".instruction").length;
            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                new mdb.Input(formOutline).init();
            });
        }
    });

    //Once remove ingredient button is clicked
    $(".ingredient_field_wrapper").click(function (e) {
        e.preventDefault();
        $(this).parent('div').remove(); //Remove field html
        ingredientInputs = $(".ingredient").length;
    });

    //Once remove instruciton button is clicked
    $(".delete_instruction_button").click(function (e) {
        e.preventDefault();
        $(this).prev().children().last().remove(); //Remove field html
        instructionInputs = $(".instruction").length;
    });
});