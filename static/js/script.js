// Dynamic input function taken and adapted from https://www.codexworld.com/add-remove-input-fields-dynamically-using-jquery/

$(document).ready(function () {
    const maxFieldIngredients = 15; //Input fields increment limitation
    const maxFieldInstructions = 10; //Input fields increment limitation
    let ingredientInputs = 1; //Initial field counter is 1
    let instructionInputs = 1; //Initial field counter is 1

    //Once add button is clicked
    $(".add_ingredient_button").click(function () {
        //Check maximum number of input fields
        if (ingredientInputs < maxFieldIngredients) {
            ingredientInputs++; //Increment field counter
            $('.ingredient_field_wrapper').append(`
            <div class="form-outline form-white mb-4">
                <input type="text" name="ingredient${ingredientInputs}" id="ingredient${ingredientInputs}" class="form-control" required />
                <label class="form-label" for="ingredient${ingredientInputs}">Ingredient</label>
                <a href="javascript:void(0);" class="remove_button" title="Add field"><i class="fas fa-minus"></i></a>
            </div>
            `)
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
                <input type="text" name="instruction${ingredientInputs}" id="instruction${ingredientInputs}" class="form-control" required />
                <label class="form-label" for="instruction${ingredientInputs}">Instruction ${ingredientInputs}</label>
                <a href="javascript:void(0);" class="remove_button" title="Add field"><i class="fas fa-minus"></i></a>
            </div>
            `)
            document.querySelectorAll('.form-outline').forEach((formOutline) => {
                new mdb.Input(formOutline).init();
            });
        }
    });

    //Once remove button is clicked
    $(".ingredient_field_wrapper").on('click', '.remove_button', function (e) {
        e.preventDefault();
        $(this).parent('div').remove(); //Remove field html
        ingredientInputs--; //Decrement field counter
    });

    //Once remove button is clicked
    $(".instruction_field_wrapper").on('click', '.remove_button', function (e) {
        e.preventDefault();
        $(this).parent('div').remove(); //Remove field html
        instructionInputs--; //Decrement field counter
    });
});