var drafts = (function () {
    var fn = {
        // the key that the drafts are stored under.
        KEY: "drafts",

        // create a new UNIQUE key to use.
        createKey: function () {
            // use the base16 of the current time + a random string to reduce
            // collisions to essentially zero.
            return new Date().getTime().toString(16) + "-" + Math.random().toString(16).split(/\./).pop();
        },

        addDraft: function (drafts, stream, topic, draft) {
            var id = fn.createKey();

            drafts[id] = {
                stream: stream,
                topic: topic,
                draft: draft
            };

            return id;
        },

        editDraft: function (id, draft) {
            if (drafts[id]) {
                drafts[id].draft = draft;
            }
        },

        deleteDraft: function (id) {
            delete drafts[id];
        },

        getDraft: function (id) {
            return drafts[id] || false;
        },

        createEmptyDrafts: function () {
            return {
                streams: {},
                private: {}
            };
        }
    };

    // ls = a `localstorage` instance.
    return function (ls, version) {
        if (typeof version !== "undefined") {
            ls.version = version;
        }

        var drafts = ls.get(fn.KEY) || fn.createEmptyDrafts();

        var prototype = {
            addDraft: function (stream, topic, draft) {
                return fn.addDraft(drafts, stream, topic, draft);
            },
            editDraft: function (stream, topic, id, draft) {
                fn.editDraft(drafts, stream, topic, id, draft);
            },
            deleteDraft: function (stream, topic, id) {
                fn.deleteDraft(drafts, stream, topic, id);
            },
            delete: function () {
                drafts = fn.createEmptyDrafts();
                ls.set(fn.KEY, drafts);
            },
            save: function () {
                ls.set(fn.KEY, drafts);
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

if (typeof module !== 'undefined') {
    module.exports = drafts;
}
