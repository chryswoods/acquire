
Acquire.Login = {};

Acquire.Login._panels = {};
Acquire.Login._handles = {};
Acquire.Login._forms = {};
Acquire.Login._reminders = {};

Acquire.Login.initialise = function()
{
    // create a Wallet which will be used for the login
    let wallet = new Acquire.Wallet();

    let panels = ["url", "userpassword", "otpcode", "success",
                  "fail", "progress"];

    /* Find all of the panels in the html page and initially set them
       as invisible. Also locate all of the forms and all of the reminders */
    panels.forEach(function(panel)
    {
        let panel_element = document.getElementById(`acquire.${panel}.panel`);
        //panel_element.style.display = "none";
        Acquire.Login._panels[panel] = panel_element;

        let form_element = document.getElementById(`acquire.${panel}.form`);

        if (form_element)
        {
            Acquire.Login._forms[panel] = form_element;
        }
    });

    // now find all of the reminder elements
    let reminders = ["url", "username", "password", "otpcode"];

    reminders.forEach(function(reminder)
    {
        let reminder_element = document.getElementById(
                                            `acquire.${reminder}.reminder`);

        if (reminder_element)
        {
            Acquire.Login._reminders[reminder] = reminder_element;

            //make sure that the reminder is initially invisible
            reminder_element.style.display = "none";
        }
    });

    // now create all of the form handlers
    let handle_url_form = async function(event)
    {
        let form = Acquire.Login._forms["url"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);
    }
    Acquire.Login._handles["url"] = handle_url_form;

    let handle_userpassword_form = async function(event)
    {
        let form = Acquire.Login._forms["userpassword"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);
    }
    Acquire.Login._handles["userpassword"] = handle_userpassword_form;

    let handle_otpcode_form = async function(event)
    {
        let form = Acquire.Login._forms["otpcode"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);

        let remind_input = Acquire.Login._reminders["otpcode"];

        // make sure that we have everything we need...
        if (data["otpcode"])
        {
            if (remind_input){ remind_input.style.display = "none"; }
            let otpcode = data["otpcode"];
            let remember_device = data["remember_device"];

            console.log("submitting");
            let result = await Acquire.Login.submit_otp(wallet, otpcode,
                                                        remember_device);
            console.log("result");
        }
        else
        {
            if (remind_input){ remind_input.style.display = "inline"; }
        }
    }
    Acquire.Login._handles["otpcode"] = handle_otpcode_form;

    let handle_success_form = async function(event)
    {
        let form = Acquire.Login._forms["success"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);
    }
    Acquire.Login._handles["success"] = handle_success_form;

    let handle_fail_form = async function(event)
    {
        let form = Acquire.Login._forms["fail"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);
    }
    Acquire.Login._handles["fail"] = handle_fail_form;

    let handle_progress_form = async function(event)
    {
        let form = Acquire.Login._forms["progress"];
        let data = Acquire.Form.getFormSubmitData(form, event);
        console.log(data);
    }
    Acquire.Login._handles["progress"] = handle_fail_form;

    // associate all of the form "submit" handlers with the forms
    Object.keys(Acquire.Login._handles).forEach(function(key)
    {
        try
        {
            Acquire.Login._forms[key].addEventListener(
                                    "submit", Acquire.Login._handles[key]);
        }
        catch(err)
        {
            console.log(`ERROR ADDING EVENT LISTENER FOR FORM ${key}`);
            console.log(err);
        }
    });
}
