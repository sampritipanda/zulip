var drafts = (function () {

var exports = {};

var Draft = (function () {
    var fn = {
        // the key that the drafts are stored under.
        KEY: "drafts",

        // create a new UNIQUE key to use.
        createKey: function () {
            // use the base16 of the current time + a random string to reduce
            // collisions to essentially zero.
            return new Date().getTime().toString(16) + "-" + Math.random().toString(16).split(/\./).pop();
        },

        addDraft: function (drafts, draft) {
            var id = fn.createKey();

            draft.updatedAt = new Date().getTime();
            drafts[id] = draft;

            return id;
        },

        editDraft: function (drafts, id, draft) {
            if (drafts[id]) {
                draft.updatedAt = new Date().getTime();
                drafts[id] = draft;
            }
        },

        deleteDraft: function (drafts, id) {
            delete drafts[id];
        },

        getDraft: function (drafts, id) {
            return drafts[id] || false;
        },

        createEmptyDrafts: function () {
            return {};
        }
    };

    // ls = a `localstorage` instance.
    return function (ls, version) {
        if (typeof version !== "undefined") {
            ls.version = version;
        }

        var drafts = ls.get(fn.KEY) || fn.createEmptyDrafts();

        var prototype = {
            addDraft: function (draft) {
                return fn.addDraft(drafts, draft);
            },
            editDraft: function (id, draft) {
                fn.editDraft(drafts, id, draft);
            },
            deleteDraft: function (id) {
                fn.deleteDraft(drafts, id);
            },
            delete: function () {
                drafts = fn.createEmptyDrafts();
                ls.set(fn.KEY, drafts);
            },
            save: function () {
                ls.set(fn.KEY, drafts);
            },
            getDraft: function (id) {
                return fn.getDraft(drafts, id);
            },
            get: function () {
                return drafts;
            },
            migrate: function (v1, v2, callback) {
                drafts = ls.migrate(fn.KEY, v1, v2, callback) || fn.createEmptyDrafts();
                ls.version = v2;

                return drafts;
            }
        };

        // set a new master version for the LocalStorage instance.
        Object.defineProperty(prototype, "version", {
            get: function () {
                return ls.version;
            },
            set: function (version) {
                ls.version = version;
                drafts = ls.get(fn.KEY);

                return prototype;
            }
        });

        return prototype;
    };
}());

var ls = localstorage();
var draft_model = Draft(ls, 1);
exports.draft_model = draft_model;

exports.update_draft = function () {
    var draft = compose.snapshot_message();
    var draft_id = $("#new_message_content").data("draft-id");

    if (draft_id !== undefined) {
        if (draft !== undefined) {
            draft_model.editDraft(draft_id, draft);
        } else {
            draft_model.deleteDraft(draft_id);
        }
    } else {
        if (draft !== undefined) {
            var new_draft_id = draft_model.addDraft(draft);
            $("#new_message_content").data("draft-id", new_draft_id);
            draft_model.save();
        }
    }
};

exports.delete_draft_after_send = function () {
    var draft_id = $("#new_message_content").data("draft-id");
    if (draft_id) {
        draft_model.deleteDraft(draft_id);
    }
    $("#new_message_content").removeData("draft-id");
};

exports.restore_draft = function (draft_id) {
    var draft = draft_model.getDraft(draft_id);
    if (!draft) {
        return;
    }

    var draft_copy = _.extend({}, draft);
    if ((draft_copy.type === "stream" &&
         draft_copy.stream.length > 0 &&
             draft_copy.subject.length > 0) ||
                 (draft_copy.type === "private" &&
                  draft_copy.reply_to.length > 0)) {
        draft_copy = _.extend({replying_to_message: draft_copy},
                              draft_copy);
    }

    $("#draft_overlay").fadeOut(500, function () {
        hashchange.exit_settings();

        compose_fade.clear_compose();
        if (draft.type === "stream") {
            if (draft.stream === "") {
                draft_copy.subject = "";
                narrow.activate([]);
            } else {
                narrow.activate([{operator: "stream", operand: draft.stream}, {operator: "topic", operand: draft.subject}],
                                {select_first_unread: true, trigger: "restore draft"});
            }
        } else {
            if (draft.private_message_recipient === "") {
                narrow.activate([{operator: "is", operand: "private"}],
                                {select_first_unread: true, trigger: "restore draft"});
            } else {
                narrow.activate([{operator: "pm-with", operand: draft.private_message_recipient}],
                                {select_first_unread: true, trigger: "restore draft"});
            }
        }
        compose.start(draft_copy.type, draft_copy);
        $("#new_message_content").data("draft-id", draft_id);
    });
};

exports.setup_page = function (callback) {
    function setup_event_handlers() {
        window.addEventListener("beforeunload", function () {
            exports.update_draft();
            exports.draft_model.save();
        });

        $("#new_message_content").focusout(exports.update_draft);

        $(".draft_controls .restore-draft").on("click", function () {
            var draft_row = $(this).closest(".draft-row");
            var draft_id = draft_row.data("draft-id");

            exports.restore_draft(draft_id);
        });

        $(".draft_controls .delete-draft").on("click", function () {
            var draft_row = $(this).closest(".draft-row");
            var draft_id = draft_row.data("draft-id");

            exports.draft_model.deleteDraft(draft_id);
            draft_row.remove();

            if ($("#drafts_table .draft-row").length === 0) {
                $('#drafts_table .no-drafts').show();
            }
        });
    }

    function format_drafts(data) {
        var drafts = _.mapObject(data, function (draft, id) {
            var formatted;
            if (draft.type === "stream") {
                formatted = {
                    draft_id: id,
                    is_stream: true,
                    stream: draft.stream,
                    stream_color: stream_data.get_color(draft.stream),
                    topic: draft.subject,
                    content: echo.apply_markdown(draft.content)
                };
            } else {
                var emails = util.extract_pm_recipients(draft.private_message_recipient);
                var recipients = _.map(emails, function (email) {
                    email = email.trim();
                    var person = people.get_by_email(email);
                    if (person !== undefined) {
                        return person.full_name;
                    }
                    return email;
                }).join(', ');

                formatted = {
                    is_stream: false,
                    recipients: recipients,
                    content: echo.apply_markdown(draft.content)
                };
            }
            return formatted;
        });
        return drafts;
    }

    function _populate_and_fill() {
        $('#drafts_table').empty();
        var drafts = format_drafts(draft_model.get());
        var rendered = templates.render('draft_table_body', { drafts: drafts });
        $('#drafts_table').append(rendered);
        if ($("#drafts_table .draft-row").length > 0) {
            $('#drafts_table .no-drafts').hide();
        }

        if (callback) {
            callback();
        }

        setup_event_handlers();
    }

    function populate_and_fill() {
        i18n.ensure_i18n(function () {
            _populate_and_fill();
        });
    }
    populate_and_fill();
};

exports.launch = function () {
    exports.setup_page(function () {
        $("#draft_overlay").fadeIn(300);
    });
};

return exports;

}());
if (typeof module !== 'undefined') {
    module.exports = drafts;
}
