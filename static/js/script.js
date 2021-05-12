$(document).ready(function () {

    // Dynamic input function taken and adapted from https://www.codexworld.com/add-remove-input-fields-dynamically-using-jquery/
    const maxFieldIngredients = 20; //Input fields increment limitation
    const maxFieldInstructions = 10; //Input fields increment limitation
    let ingredientInputs = $(".ingredient").length; //Initial field counter is amount of nodes
    let instructionInputs = $(".instruction").length; //Initial field counter is amount of nodes

    //Once add button is clicked
    $(".add_ingredient_button").click(function () {
        //Check maximum number of input fields
        if (ingredientInputs < maxFieldIngredients) {
            ingredientInputs++; //Increment field counter
            $('.ingredient_field_wrapper').append(`
            <div class="form-outline mb-4">
                <input type="text" name="ingredient" id="ingredient${ingredientInputs}" class="form-control ingredient" required />
                <label class="form-label" for="ingredient${ingredientInputs}">Ingredient</label>
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
            <div class="form-outline mb-4">
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
    $(".delete_ingredient_button").click(function (e) {
        e.preventDefault();
        $(this).parent().prev().children().last().remove(); //Remove field html
        ingredientInputs = $(".ingredient").length;
    });

    //Once remove instruciton button is clicked
    $(".delete_instruction_button").click(function (e) {
        e.preventDefault();
        $(this).parent().prev().children().last().remove(); //Remove field html
        instructionInputs = $(".instruction").length;
    });


    // cloudinary widget
    $(".photo-widget").click(e => {
        e.preventDefault();
        cloudinary.openUploadWidget({
            cloud_name: 'dljklwibk',
            upload_preset: 'veggie',
            sources: ['local', 'url', 'google_drive', 'dropbox', 'shutterstock', 'instagram']
        }, (error, result) => {
            if (!error && result && result.event === "success") {
                console.log(result.info.secure_url);
                $("#image_submit").val(result.info.secure_url);
                $(".image-submit-div").append(`
                    <p><i class="fas fa-check-circle"></i> ${result.info.secure_url}</p>
                `)
                $(".photo-widget").remove();
            }
        });
    });

    // changes appearance of favorite button on hover
    $(".favorite").hover(
        function () {
            $(this).addClass("fas");
        },
        function () {
            $(this).removeClass("fas");
        });

    $(".remove").hover(
        function () {
            $(this).removeClass("fas");
            $(this).addClass("far");
        },
        function () {
            $(this).removeClass("far");
            $(this).addClass("fas");
        });

    // checks if passwords match on registration form
    function checkPasswordMatch() {
        let password = $("#password").val();
        let confirmPassword = $("#passwordconfirm").val();

        if (password.length == 0) {
            $("#passwordmatch").html("Password field empty");
            $("#register-submit").prop("disabled", true);
        } else if (password != confirmPassword) {
            $("#passwordmatch").html("Passwords do not match!");
            $("#register-submit").prop("disabled", true);
        } else if (password.length <= 4 ) {
            $("#passwordmatch").html("Password must be at least 5 characters long");
            $("#register-submit").prop("disabled", true);
        } else {
            $("#passwordmatch").html("Passwords match.");
            $("#register-submit").prop("disabled", false);
        }
    }

    checkPasswordMatch()

    $("#password, #passwordconfirm").keyup(checkPasswordMatch);

});