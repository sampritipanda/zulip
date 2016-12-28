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

            if (!drafts.streams[stream]) {
                drafts.streams[stream] = {};
            }

            if (!drafts.streams[stream][topic]) {
                drafts.streams[stream][topic] = {};
            }

            drafts.streams[stream][topic][id] = draft;

            return id;
        },

        editDraft: function (drafts, stream, topic, id, draft) {
            if (drafts.streams[stream] && drafts.streams[stream][topic]) {
                drafts.streams[stream][topic][id] = draft;
            }
        },

        deleteDraft: function (drafts, stream, topic, id) {
            if (drafts.streams[stream] && drafts.streams[stream][topic]) {
                delete drafts.streams[stream][topic][id];
            }
        },

        getDraft: function (drafts, stream, topic, id) {
            if (drafts.streams[stream] && drafts.streams[stream][topic]) {
                return drafts.streams[stream][topic][id];
            }

            return false;
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
