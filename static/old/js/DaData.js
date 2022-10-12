/**
 * Created by ipman on 01.02.2016.
 */

function join(arr /*, separator */) {
    var separator = arguments.length > 1 ? arguments[1] : ", ";
    return arr.filter(function(n){return n}).join(separator);
}

function typeDescription(type) {
    var TYPES = {
        'INDIVIDUAL': 'Индивидуальный предприниматель',
        'LEGAL': 'Организация'
    }
    return TYPES[type];
}

function showSuggestionParty(suggestion) {
    console.log(suggestion);
    var data = suggestion.data;
    if (!data)
        return;

    if (data.name && data.name.full)
        $("#id_NameClient_full").val(join([data.name.full], " "));
        $("#id_OKOPF").val(join([data.opf.code], " "));

    if (data.name)
        $("#id_NameClient_short").val(join([data.opf && data.opf.short || "", data.name.short || data.name.full], " "));

    if (data.management.name)
        $("#id_Management_post").val(join([data.management.post], " "));
        $("#id_Management_name").val(join([data.management.name], " "));

    $("#id_INN").val(join([data.inn], " / "));
    $("#id_OGRN").val(join([data.ogrn], " / "));
    $("#id_OKPO").val(join([data.okpo], " / "));
    $("#id_OKVED").val(join([data.okved], " / "));

    if (data.address)
      $("#id_Address_reg").val(join([data.postal_code, unrestricted_value]));
}

function showSuggestionPostalAddress(suggestion) {
    console.log(suggestion);
    var data = suggestion.data;
    if (!data)
        return;
    $("#id_Address_post").val(join([data.postal_code, unrestricted_value]));
}

function showSuggestionBanki(suggestion) {
    console.log(suggestion);
    var data = suggestion.data;
    if (!data)
        return;
    $("#bank_details").val(data.name && data.name.payment+"\nКор.счет: "+data.correspondent_account+"\nБИК: "+data.bic+"\nОКПО: "+data.okpo+"\nАдрес: "+data.address.value || "");
}

$("#party").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "PARTY",
    count: 5,
  /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: showSuggestionParty
});

$("#id_Address_post").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "ADDRESS",
    count: 5,
    /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: showSuggestionPostalAddress
});

$("#id_Address_residence").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "ADDRESS",
    count: 5,
    /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#id_Address_reg").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "ADDRESS",
    count: 5,
    /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#id_AddressObject").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "ADDRESS",
    count: 5,
    /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#id_Management_name").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "NAME",
    count: 5,
       /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#id_Founder_FIO").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "NAME",
    count: 5,
       /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#id_Person_FIO").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "NAME",
    count: 5,
       /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: function(suggestion) {
        console.log(suggestion);
    }
});

$("#bank").suggestions({
    serviceUrl: "https://dadata.ru/api/v2",
    token: "6217fdd8f6360d58dea99eaa3b230271a2f340d8",
    type: "BANK",
    count: 5,
    /* Вызывается, когда пользователь выбирает одну из подсказок */
    onSelect: showSuggestionBanki
});