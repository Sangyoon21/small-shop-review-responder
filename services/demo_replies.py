"""Pre-written replies for the SYNTHETIC demo reviews (offline demo only).

Two versions per review x language x tone, so "Regenerate" and the tone and
language settings visibly work without an API key. Written by the project
team to follow the same reply rules as the live AI (specific, no invented
facts, no compensation offers, serious complaints moved offline).

Keyed by demo review number (1-5) -> language -> tone -> [version 1, version 2].
"""

from __future__ import annotations

EMAIL = "hello@cornichebean.example"
SIGN_EN = "— The Corniche Bean team"
SIGN_AR = "— فريق كورنيش بين"

DEMO_REPLY_VARIANTS: dict[int, dict[str, dict[str, list[str]]]] = {
    # 1. Mariam K. — 5★, English: karak, saffron cake, barista Rami, terrace sea view.
    1: {
        "en": {
            "friendly": [
                "Mariam, this made our day! We're so glad the saffron cake hit the right sweetness and "
                "that Rami remembered your order — he'll be thrilled to hear it. The terrace at sunset "
                f"is our favourite spot too. See you for another karak soon! {SIGN_EN}",
                "Thank you, Mariam! \"Best karak on the Corniche\" is going straight onto our staff "
                "noticeboard. Rami loves getting to know our regulars, and we're happy the saffron cake "
                f"was just the right sweetness. Enjoy the sea breeze on the terrace next time too! {SIGN_EN}",
            ],
            "professional": [
                "Thank you, Mariam, for the generous review. We're pleased the karak and saffron cake "
                "lived up to your expectations, and we'll pass your kind words on to Rami, who takes "
                f"pride in knowing our guests. We look forward to welcoming you back to the terrace. {SIGN_EN}",
                "Mariam, thank you for taking the time to share this. It's great to hear the saffron cake "
                "was moist and well balanced, and that Rami made your second visit feel personal. We hope "
                f"to see you again for an evening on the terrace. {SIGN_EN}",
            ],
            "formal": [
                "Dear Mariam, thank you for your kind review. We are delighted that you enjoyed our karak "
                "and saffron cake, and we will gladly share your compliments with Rami. It would be our "
                f"pleasure to welcome you back to the terrace in the evening. {SIGN_EN}",
                "Dear Mariam, we sincerely appreciate your words. It is gratifying to know that the saffron "
                "cake suited your taste and that our team made you feel recognised on your second visit. "
                f"We look forward to serving you again. {SIGN_EN}",
            ],
        },
        "ar": {
            "friendly": [
                "مريم، أسعدتنا كلماتك! يسعدنا أن كيكة الزعفران كانت بحلاوة مناسبة، وأن رامي تذكّر طلبك — "
                "سيفرح كثيراً بذلك. الجلسة على التراس وقت الغروب هي المفضلة لدينا أيضاً. ننتظرك لكوب كرك "
                f"آخر قريباً! {SIGN_AR}",
                "شكراً يا مريم! وصفك لكركنا بأنه الأفضل على الكورنيش أسعد الفريق كله، ورامي فرح جداً بأنه "
                "تذكّر طلبك. يسعدنا أن كيكة الزعفران أعجبتك، ونتمنى أن نراك قريباً على التراس مع نسمة البحر. "
                f"{SIGN_AR}",
            ],
            "professional": [
                "شكراً لكِ يا مريم على هذا التقييم الجميل. يسعدنا أن الكرك وكيكة الزعفران نالا إعجابك، "
                "وسننقل كلماتك الطيبة إلى رامي الذي يحرص على معرفة ضيوفنا. نتطلع إلى استقبالك مجدداً على "
                f"التراس. {SIGN_AR}",
                "مريم، نشكرك على مشاركة تجربتك. يسرّنا أن كيكة الزعفران كانت طرية ومتوازنة الحلاوة، وأن رامي "
                f"جعل زيارتك الثانية مميزة. نأمل أن نراك قريباً في أمسية على التراس. {SIGN_AR}",
            ],
            "formal": [
                "السيدة مريم، نتقدم إليكِ بخالص الشكر على تقييمك الكريم. يسعدنا أن الكرك وكيكة الزعفران قد "
                "نالا استحسانك، وسننقل إطراءك إلى الزميل رامي. ويشرّفنا استقبالك مجدداً على التراس في المساء. "
                f"{SIGN_AR}",
                "السيدة مريم، نثمّن كلماتك الطيبة عالياً. ويسرّنا أن كيكة الزعفران قد وافقت ذوقك، وأن فريقنا "
                f"قد أحسن استقبالك في زيارتك الثانية. نتطلع إلى خدمتك مرة أخرى. {SIGN_AR}",
            ],
        },
    },
    # 2. Daniel P. — 3★, English: great shakshuka + portions; 25-min Friday wait; asked twice for water.
    2: {
        "en": {
            "friendly": [
                "Daniel, thank you for the kind words about the shakshuka and portions. You're right that "
                "a 25-minute wait and asking twice for water isn't the Friday experience we want — Friday "
                "mornings are our busiest time and we're looking at how we handle the rush. We'd love to "
                f"welcome you back, busy day or quiet. {SIGN_EN}",
                "Thanks, Daniel — glad the shakshuka won you over! Waiting nearly 25 minutes and having to "
                "ask twice for water isn't okay, even on a packed Friday morning, and we've shared your "
                f"comments with the team. Hope to see you again soon, whichever day suits you. {SIGN_EN}",
            ],
            "professional": [
                "Daniel, thank you for the honest review. We're glad the shakshuka and portion sizes stood "
                "out. A 25-minute wait and repeated requests for water fall short of our standards, and "
                f"Friday mornings are a pressure point we're working on. We hope to welcome you back soon. {SIGN_EN}",
                "Daniel, we appreciate you sharing both sides of your visit. It's good to hear the shakshuka "
                "was delicious and generous, and we're sorry the wait was so long and that you had to ask "
                f"twice for water. We've shared this with our team to handle Friday mornings better. {SIGN_EN}",
            ],
            "formal": [
                "Dear Daniel, thank you for your candid review. We are pleased that you enjoyed the "
                "shakshuka and found the portions generous. We apologise for the long wait and for the need "
                "to ask twice for water; Friday mornings are our busiest period, and we are working to serve "
                f"our guests more promptly. We hope to welcome you again. {SIGN_EN}",
                "Dear Daniel, we appreciate your balanced account of your visit. While we are glad the "
                "shakshuka met your expectations, a wait of almost 25 minutes is not the standard we aim "
                f"for, and we regret the slow service. Your comments have been shared with our team. {SIGN_EN}",
            ],
        },
        "ar": {
            "friendly": [
                "دانيال، شكراً على كلماتك الطيبة عن الشكشوكة وحجم الأطباق. معك حق، فالانتظار ٢٥ دقيقة وطلب "
                "الماء مرتين ليس التجربة التي نريدها صباح الجمعة، وهو أكثر أوقاتنا ازدحاماً، ونعمل على تحسين "
                f"تعاملنا مع هذا الضغط. يسعدنا استقبالك مجدداً في أي يوم. {SIGN_AR}",
                "شكراً يا دانيال، يسعدنا أن الشكشوكة نالت إعجابك! الانتظار قرابة ٢٥ دقيقة وطلب الماء مرتين أمر "
                "لا نرضاه حتى في زحمة صباح الجمعة، وقد شاركنا ملاحظتك مع الفريق. نتمنى أن نراك قريباً في اليوم "
                f"الذي يناسبك. {SIGN_AR}",
            ],
            "professional": [
                "دانيال، نشكرك على تقييمك الصريح. يسعدنا أن الشكشوكة وحجم الأطباق نالا رضاك، ونعتذر عن "
                "الانتظار الطويل وتكرار طلب الماء، فهذا أقل من المستوى الذي نسعى إليه. صباح الجمعة هو الأكثر "
                f"ازدحاماً لدينا ونعمل على تحسين الخدمة فيه. {SIGN_AR}",
                "دانيال، نقدّر مشاركتك لجوانب زيارتك كلها. يسرّنا أن الشكشوكة كانت لذيذة والأطباق وافرة، ونأسف "
                "لطول الانتظار ولاضطرارك لطلب الماء مرتين. وقد نقلنا ملاحظتك إلى الفريق لنحسن التعامل مع زحمة "
                f"صباح الجمعة. {SIGN_AR}",
            ],
            "formal": [
                "السيد دانيال، نشكركم على تقييمكم الصريح. يسعدنا أن الشكشوكة قد نالت استحسانكم، ونعتذر عن طول "
                "الانتظار وعن اضطراركم لطلب الماء مرتين. إن صباح الجمعة هو أكثر أوقاتنا ازدحاماً، ونعمل على "
                f"تقديم خدمة أسرع لضيوفنا. ونأمل أن نتشرف بزيارتكم مجدداً. {SIGN_AR}",
                "السيد دانيال، نثمّن عرضكم المتوازن لتجربتكم. ومع سرورنا بأن الشكشوكة كانت على مستوى توقعاتكم، "
                "فإن انتظار قرابة خمس وعشرين دقيقة لا يليق بالمستوى الذي نسعى إليه، وقد أُبلغ فريقنا بملاحظاتكم. "
                f"{SIGN_AR}",
            ],
        },
    },
    # 3. Faisal A. — 1★, English: hair in sandwich, cashier shrugged, stomach ache. Serious: move offline.
    3: {
        "en": {
            "friendly": [
                "Faisal, we're sorry to read this. What you describe is not acceptable to us, and the "
                "response at the counter should have been very different. We take food-safety concerns "
                f"seriously and want to look into what happened. Please email us at {EMAIL} so the owner "
                f"can speak with you directly. {SIGN_EN}",
                "Faisal, we're really sorry your visit went this way, and that you felt unwell afterwards. "
                "Being met with a shrug when you raised it is not how our team should respond. We'd like to "
                f"understand exactly what happened — please email the owner at {EMAIL}. {SIGN_EN}",
            ],
            "professional": [
                "Faisal, thank you for letting us know, and we're sorry to hear you felt unwell. Food-safety "
                "concerns are taken very seriously here, and a concern raised at the counter deserves a "
                f"proper response. Please contact us at {EMAIL} so the owner can follow up with you "
                f"personally. {SIGN_EN}",
                "Faisal, we're concerned to read about your experience and sorry you had a difficult "
                "evening. We want to look into this properly, including how it was handled at the counter. "
                f"Please email {EMAIL} with the date of your visit so the owner can contact you. {SIGN_EN}",
            ],
            "formal": [
                "Dear Faisal, we are sorry to learn of your experience and that you felt unwell afterwards. "
                "We treat every food-safety concern with the utmost seriousness, and the response you "
                f"received at the counter did not reflect our standards. We kindly ask you to contact us at "
                f"{EMAIL} so that the owner may speak with you directly. {SIGN_EN}",
                "Dear Faisal, thank you for bringing this matter to our attention. We regret that your visit "
                "was so disappointing and that you were unwell that evening. We would like to look into this "
                f"fully; please write to us at {EMAIL} at your convenience. {SIGN_EN}",
            ],
        },
        "ar": {
            "friendly": [
                "فيصل، يؤسفنا ما قرأناه. ما وصفته غير مقبول بالنسبة لنا، وكان يجب أن يكون التعامل عند "
                "الكاشير مختلفاً تماماً. نأخذ ملاحظات سلامة الطعام بجدية ونريد التحقق مما حدث. نرجو مراسلتنا "
                f"على {EMAIL} ليتواصل معك المالك مباشرة. {SIGN_AR}",
                "فيصل، نأسف جداً لما مررت به ولأنك لم تكن بخير بعد زيارتك. ولم يكن من المفترض أن تُقابَل "
                "ملاحظتك بعدم اكتراث عند الكاشير. نريد أن نفهم ما حدث بالتفصيل، فنرجو مراسلة المالك على "
                f"{EMAIL}. {SIGN_AR}",
            ],
            "professional": [
                "فيصل، نشكرك على إبلاغنا ونأسف لأنك شعرت بتوعك. نتعامل مع أي ملاحظة تخص سلامة الطعام بجدية "
                "كبيرة، وكان يجب أن تلقى ملاحظتك عند الكاشير اهتماماً حقيقياً. نرجو التواصل معنا على "
                f"{EMAIL} ليتابع المالك الأمر معك شخصياً. {SIGN_AR}",
                "فيصل، يقلقنا ما قرأناه ونأسف لأمسيتك الصعبة. نريد التحقق من الأمر بشكل كامل، بما في ذلك "
                f"طريقة التعامل معك عند الكاشير. نرجو مراسلتنا على {EMAIL} مع تاريخ زيارتك ليتواصل معك "
                f"المالك. {SIGN_AR}",
            ],
            "formal": [
                "السيد فيصل، يؤسفنا ما تعرضتم له وشعوركم بالتوعك بعد زيارتكم. إننا نتعامل مع كل ما يتعلق "
                "بسلامة الغذاء بأقصى درجات الجدية، ولم يكن التعامل الذي لقيتموه عند الكاشير على المستوى "
                f"المطلوب. نرجو التكرم بالتواصل معنا عبر {EMAIL} ليتحدث إليكم المالك مباشرة. {SIGN_AR}",
                "السيد فيصل، نشكركم على إطلاعنا على هذا الأمر، ونأسف لأن زيارتكم كانت مخيبة للآمال وأنكم لم "
                f"تكونوا بخير في تلك الليلة. نود التحقق من الأمر بشكل كامل، فنرجو مراسلتنا على {EMAIL} في "
                f"الوقت الذي يناسبكم. {SIGN_AR}",
            ],
        },
    },
    # 4. Noura — 5★, Arabic: Arabic coffee, fresh dates, outdoor seating at sunset, respectful fast staff.
    4: {
        "ar": {
            "friendly": [
                "أهلاً نورة، أسعدتنا كلماتك! يسعدنا أن القهوة العربية والتمر نالا إعجابك، وأن الجلسة الخارجية "
                f"وقت المغرب كانت على ذوقك. سننقل شكرك للفريق، وننتظر زيارتك القادمة. {SIGN_AR}",
                "شكراً يا نورة على كلماتك الجميلة وتوصيتك بنا! القهوة العربية والتمر الطازج من أكثر ما نعتز به، "
                "وجلسة المغرب في الخارج لها سحر خاص فعلاً. الفريق سعيد جداً بإطرائك على سرعتهم واحترامهم. "
                f"{SIGN_AR}",
            ],
            "professional": [
                "نورة، نشكرك على تقييمك وتوصيتك الكريمة. يسعدنا أن القهوة العربية والتمر الطازج نالا رضاك، وأن "
                "الجلسة الخارجية وقت المغرب أضافت لتجربتك. وسننقل إشادتك إلى الفريق. نتطلع لزيارتك القادمة. "
                f"{SIGN_AR}",
                "نورة، تقييمك يعني لنا الكثير. يسرّنا أن خدمة الفريق كانت سريعة ومحترمة، وأن القهوة العربية "
                f"والتمر كانا على مستوى توقعاتك. ننتظرك قريباً في جلسة المغرب. {SIGN_AR}",
            ],
            "formal": [
                "السيدة نورة، نتقدم إليكِ بجزيل الشكر على تقييمك وتوصيتك. يسعدنا أن القهوة العربية والتمر قد "
                "نالا استحسانك، وأن الجلسة الخارجية وقت المغرب قد راقت لك. وسننقل ثناءك إلى فريق العمل، "
                f"ويشرّفنا استقبالك مجدداً. {SIGN_AR}",
                "السيدة نورة، نثمّن كلماتك الكريمة عالياً. ويسرّنا أن فريقنا قد حظي بثقتك في حسن التعامل وسرعة "
                f"الخدمة، وأن القهوة العربية والتمر الطازج قد وافقا ذوقك. نتطلع إلى خدمتك مرة أخرى. {SIGN_AR}",
            ],
        },
        "en": {
            "friendly": [
                "Noura, your words made our day! We're delighted the Arabic coffee and fresh dates hit the "
                "spot, and that you enjoyed the outdoor seating at sunset. We'll pass your thanks on to the "
                f"team and look forward to your next visit. {SIGN_EN}",
                "Thank you, Noura, for the lovely review and the recommendation! Our Arabic coffee and fresh "
                "dates are a point of pride, and there's nothing quite like sitting outside at sunset. The "
                f"team was thrilled to read your kind words about them. {SIGN_EN}",
            ],
            "professional": [
                "Noura, thank you for the review and your recommendation. We're pleased the Arabic coffee and "
                "fresh dates were to your liking and that the outdoor seating at sunset added to your visit. "
                f"We'll share your praise with the team and look forward to seeing you again. {SIGN_EN}",
                "Noura, your review means a lot to us. It's good to hear our team was quick and respectful, "
                "and that the Arabic coffee and dates met your expectations. We hope to welcome you back for "
                f"another sunset soon. {SIGN_EN}",
            ],
            "formal": [
                "Dear Noura, thank you sincerely for your review and recommendation. We are delighted that "
                "you enjoyed our Arabic coffee and dates, and the outdoor seating at sunset. We will gladly "
                f"convey your compliments to our team and would be honoured to welcome you again. {SIGN_EN}",
                "Dear Noura, we greatly appreciate your generous words. It is a pleasure to know that our "
                "team's courtesy and prompt service met your expectations, and that our Arabic coffee and "
                f"fresh dates suited your taste. We look forward to serving you again. {SIGN_EN}",
            ],
        },
    },
    # 5. Khalid M. — 2★, Arabic: nice place; rude staff on table change; shouting; high prices. Staff misconduct.
    5: {
        "ar": {
            "friendly": [
                "أخي خالد، نشكرك على صراحتك ونعتذر عن الطريقة التي عوملتم بها. ما وصفته لا يعكس الأسلوب الذي "
                f"نريده لضيوفنا، وسنراجع الأمر مع الفريق. نرجو التواصل معنا عبر {EMAIL} لنستمع إليك بشكل "
                f"مباشر. {SIGN_AR}",
                "خالد، يسعدنا أن المكان أعجبك، لكننا نأسف حقاً لما حدث عند طلبكم تغيير الطاولة. لا نريد لأي ضيف "
                "أن يشهد صراخاً أو تعاملاً غير لائق، وقد أخذنا ملاحظتك بجدية. يسعدنا أن تراسلنا على "
                f"{EMAIL} لنفهم ما حدث. {SIGN_AR}",
            ],
            "professional": [
                "خالد، نشكرك على ملاحظتك الصريحة ونعتذر عن التعامل الذي واجهتموه. نحرص على أن يُعامل كل ضيف "
                "باحترام، وسنراجع ما ذكرته مع الفريق، كما نأخذ ملاحظتك حول الأسعار مقارنة بالخدمة بعين "
                f"الاعتبار. نرجو التواصل معنا عبر {EMAIL}. {SIGN_AR}",
                "خالد، نأسف لأن زيارتكم لم تكن على المستوى المتوقع. ما وصفته من تعامل عند تغيير الطاولة وصراخ "
                f"أمام الضيوف أمر نتعامل معه بجدية، ونود سماع التفاصيل منك مباشرة عبر {EMAIL}. {SIGN_AR}",
            ],
            "formal": [
                "السيد خالد، نشكركم على ملاحظاتكم، ونعتذر عن التعامل الذي لقيتموه. إن ما ذكرتموه لا يتوافق مع "
                "ما نحرص عليه من احترام لضيوفنا، وستتم مراجعته مع فريق العمل. ونرجو التكرم بالتواصل معنا عبر "
                f"{EMAIL}. {SIGN_AR}",
                "السيد خالد، نأسف لما واجهتموه خلال زيارتكم، ونقدّر إطلاعنا عليه. إننا نولي حسن التعامل مع "
                f"ضيوفنا أهمية قصوى، ونود الاستماع إلى تفاصيل ما حدث مباشرة عبر {EMAIL}. {SIGN_AR}",
            ],
        },
        "en": {
            "friendly": [
                "Khalid, thank you for being candid, and we're sorry for how you were treated. What you "
                "describe doesn't reflect how we want our guests to feel, and we'll be reviewing it with the "
                f"team. Please reach out to us at {EMAIL} so we can hear from you directly. {SIGN_EN}",
                "Khalid, we're glad you liked the space, but really sorry about what happened when you asked "
                "to change tables. No guest should have to witness shouting or be spoken to rudely, and we're "
                f"taking your comments seriously. Please drop us a line at {EMAIL} so we can understand what "
                f"happened. {SIGN_EN}",
            ],
            "professional": [
                "Khalid, thank you for your candid comments, and we apologise for the treatment you received. "
                "Every guest should be treated with respect, and we will review what you describe with our "
                f"team. We also note your point about prices relative to the service. Please reach us at "
                f"{EMAIL}. {SIGN_EN}",
                "Khalid, we're sorry your visit fell short. The way you describe being treated when changing "
                "tables, and the shouting in front of guests, is something we take seriously. We'd like to "
                f"hear the details directly at {EMAIL}. {SIGN_EN}",
            ],
            "formal": [
                "Dear Khalid, thank you for your comments, and please accept our apologies for the treatment "
                "you experienced. What you describe is not consistent with the respect we owe our guests, and "
                f"it will be reviewed with our team. We kindly invite you to contact us at {EMAIL}. {SIGN_EN}",
                "Dear Khalid, we regret the experience you had during your visit and appreciate you bringing "
                "it to our attention. Courteous treatment of our guests is of the utmost importance to us, and "
                f"we would welcome the opportunity to hear the details at {EMAIL}. {SIGN_EN}",
            ],
        },
    },
}
