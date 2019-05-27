/** Below functions are all for the form-to-json code.
 *
 *  Form to JSON code is inspired heavily from excellent tutorial here
 *  https://code.lengstorf.com/get-form-values-as-json/
 */

Acquire.Form = {};

/**
  * Checks that an element has a non-empty `name` and `value` property.
  * @param  {Element} element  the element to check
  * @return {Bool}             true if the element is an input, false if not
*/
Acquire.Form.isValidElement = function (element)
{
    return element.name && element.value;
};

/**
  * Checks if an element’s value can be saved (e.g. not an unselected checkbox).
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the value should be added, false if not
*/
Acquire.Form.isValidValue = function (element)
{
    return !['checkbox', 'radio'].includes(element.type) || element.checked;
};

/**
  * Checks if an input is a checkbox, because checkboxes allow multiple values.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a checkbox, false if not
*/
Acquire.Form.isCheckbox = function (element)
{
    return element.type === 'checkbox';
};

/**
  * Checks if an input is a `select` with the `multiple` attribute.
  * @param  {Element} element  the element to check
  * @return {Boolean}          true if the element is a multiselect, false if not
*/
Acquire.Form.isMultiSelect = function (element)
{
    return element.options && element.multiple;
};

/**
  * Retrieves the selected options from a multi-select as an array.
  * @param  {HTMLOptionsCollection} options  the options for the select
  * @return {Array}                          an array of selected option values
*/
Acquire.Form.getSelectValues = function (options)
{
    return [].reduce.call(options, function (values, option) {
        return option.selected ? values.concat(option.value) : values;
    }, []);
};

/**
  * Retrieves input data from a form and returns it as a JSON object.
  * @param  {HTMLFormControlsCollection} elements  the form elements
  * @return {Object}                               form data as an object literal
  */
Acquire.Form.formToJSON = function (elements)
{
    return [].reduce.call(elements, function (data, element) {
        // Make sure the element has the required properties and
        // should be added.
        if (Acquire.Form.isValidElement(element) &&
            Acquire.Form.isValidValue(element))
        {
            /*
             * Some fields allow for more than one value, so we need to check if this
             * is one of those fields and, if so, store the values as an array.
             */
            if (Acquire.Form.isCheckbox(element))
            {
                var values = (data[element.name] || []).concat(element.value);
                if (values.length == 1)
                {
                    values = values[0];
                }
                data[element.name] = values;
            }
            else if (Acquire.Form.isMultiSelect(element))
            {
                data[element.name] = Acquire.Form.getSelectValues(element);
            }
            else
            {
                data[element.name] = element.value;
            }
        }

        return data;
    },
    {});
};

Acquire.Form.getFormSubmitData = function(form, event)
{
    // make sure that we don't submit the page as we are
    // handling the form ourselves
    event.preventDefault();
    return Acquire.Form.formToJSON(form.elements);
}
