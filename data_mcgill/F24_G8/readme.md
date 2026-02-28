Project Description
You will create the CoolSupplies application for a school. CoolSupplies is intended to be used by school
admins to effectively manage school supplies needed for students in grade 1 to 12 and parents to order
school supplies.
The CoolSupplies application has a built-in user account for the school admin called admin@cool.ca.
Initially, the password for this account is set to admin, but this can be changed later on by the person
with admin access. When a parent registers in the system, they provide an email address as the account
name and a password. The account name and password identify each parent. Optionally, a parent can
include their name and phone number. Once entered, the email address of a parent cannot be changed.
However, the school admin can delete a parent from the application.
The school admin can configure which grades are taught at the school. Different schools may use
different numbering systems for their grades (e.g., 1 to 12, A to H, etc.). The school admin also specifies a
bundle of school supplies required for each grade for a certain school year. Items in a bundle may be
characterized as mandatory, recommended, or optional. For example, a grade 1 student may need a
mandatory notepad, a certain number of recommended pencils, and an optional eraser, while a grade 5
student may need an optional notepad and a mandatory calculator. If a bundle contains at least two
individual items, then a discount may be specified by the school admin. When adding an individual item
to the school supplies of the CoolSupplies application, its name and price need to be specified. Last but
not least, the school admin enters the names of the students for each grade of the year.
After a parent has registered for the application, the parent can indicate for which student(s) they will be
ordering supplies. If a mistake is made, the parent can also deselect a previously selected student. After
the selection of the student(s), the parent may start an order, at which point the application keeps track
of the date the order was created and assigns an order number.
Then, the parent selects which and how many items and/or bundles they need for the students. If a
bundle is selected, then the parent may specify whether only mandatory, mandatory and recommended,
or all items in a bundle should be included in the order. This setting applies to all bundles in the order.
Again, if a mistake is made, the items and bundles in an order can be adjusted or removed completely.
Once the order is finalized, it needs to be paid. The CoolSupplies application does not keep track of
payment information, except for the payment’s authorization code. If the payment is not received before
the start of the school year, a penalty needs to be paid. This requires a separate transaction for which the
authorization code is also recorded. Before the start of the school year, the parent may cancel the order.
Once the order is paid, it is prepared for the student to be picked up in the school at the beginning of the
school year. When a student picks up their supplies, it is noted in the application.
The CoolSupplies application keeps track of only the current school year, i.e., at the end of a school year
all orders are removed from the application and the students and school supplies for the next year are
updated. The application offers a feature to (a) move all students to the next grade for the next school
year and (b) to increase the price of all items by a certain percentage. During the school year, the price of
school supplies does not change.