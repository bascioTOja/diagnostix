(function () {
  function getCsrfToken() {
    var cookieValue = null;
    var name = "csrftoken=";
    var cookies = document.cookie ? document.cookie.split(";") : [];
    for (var i = 0; i < cookies.length; i += 1) {
      var cookie = cookies[i].trim();
      if (cookie.substring(0, name.length) === name) {
        cookieValue = decodeURIComponent(cookie.substring(name.length));
        break;
      }
    }
    return cookieValue;
  }

  function bindToasts() {
    var toastElements = document.querySelectorAll(".toast");
    toastElements.forEach(function (el) {
      if (window.bootstrap && window.bootstrap.Toast) {
        var toast = new window.bootstrap.Toast(el, { delay: 4000 });
        toast.show();
      }
    });
  }

  function bindConfirmModal() {
    var modalElement = document.getElementById("confirmActionModal");
    if (!modalElement || !window.bootstrap || !window.bootstrap.Modal) {
      return;
    }
    var confirmModal = new window.bootstrap.Modal(modalElement);
    var confirmButton = document.getElementById("confirmActionButton");
    var activeForm = null;

    document.querySelectorAll("form[data-confirm]").forEach(function (form) {
      form.addEventListener("submit", function (event) {
        if (form.dataset.confirmed === "1") {
          return;
        }
        event.preventDefault();
        activeForm = form;
        confirmModal.show();
      });
    });

    if (confirmButton) {
      confirmButton.addEventListener("click", function () {
        if (!activeForm) {
          return;
        }
        activeForm.dataset.confirmed = "1";
        activeForm.submit();
      });
    }
  }

  function bindDynamicSlots() {
    var stationInput = document.getElementById("id_station");
    var dateInput = document.getElementById("id_booking_date");
    var slotSelect = document.getElementById("id_slot_choice");

    if (!stationInput || !dateInput || !slotSelect) {
      return;
    }

    var template = slotSelect.dataset.slotUrlTemplate;
    if (!template) {
      return;
    }

    function clearSlots() {
      slotSelect.innerHTML = "";
      var opt = document.createElement("option");
      opt.value = "";
      opt.textContent = "Wybierz slot";
      slotSelect.appendChild(opt);
    }

    function loadSlots() {
      var stationId = stationInput.value;
      var dayValue = dateInput.value;
      if (!stationId || !dayValue) {
        clearSlots();
        return;
      }

      var url = template.replace("__station_id__", stationId) + "?date=" + encodeURIComponent(dayValue);
      fetch(url, {
        method: "GET",
        headers: {
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": getCsrfToken(),
        },
      })
        .then(function (response) { return response.json(); })
        .then(function (data) {
          clearSlots();
          (data.slots || []).forEach(function (slot) {
            var option = document.createElement("option");
            option.value = slot.value;
            option.textContent = slot.label;
            slotSelect.appendChild(option);
          });
        })
        .catch(function () {
          clearSlots();
        });
    }

    stationInput.addEventListener("change", loadSlots);
    dateInput.addEventListener("change", loadSlots);

    clearSlots();
  }

  document.addEventListener("DOMContentLoaded", function () {
    bindToasts();
    bindConfirmModal();
    bindDynamicSlots();
  });
})();

